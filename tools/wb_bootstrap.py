from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
import sys

LogFn = Callable[[str], None]


class SetupStrategy(Enum):
    AUTO = "auto"
    MANAGED = "managed"
    SYSTEM = "system"

SETUP_STRATEGY_ENV = "WB_SETUP_STRATEGY"
MANAGED_PYTHON_PATH_ENV = "WB_MANAGED_PYTHON_PATH"
MANAGED_PYTHON_URL_ENV = "WB_MANAGED_PYTHON_URL"
MANAGED_PYTHON_VERSION_ENV = "WB_MANAGED_PYTHON_VERSION"
MANAGED_PYTHON_DIR_ENV = "WB_MANAGED_PYTHON_DIR"
PIP_CONSTRAINTS_ENV = "WB_PIP_CONSTRAINTS"

DEFAULT_MANAGED_PYTHON_VERSION = "3.11.9"
MIN_PYTHON_VERSION = (3, 10)
MIN_PYTHON_TEXT = "3.10"
DEFAULT_CONSTRAINTS_FILES = ("constraints.txt", "requirements.lock")


@dataclass(frozen=True)
class RuntimeStatus:
    available: bool
    python_path: Path | None = None
    detail: str | None = None


@dataclass(frozen=True)
class BootstrapContext:
    project_root: Path
    venv_dir: Path
    env_file: Path
    env_example: Path
    base_python: Path


def python_in_venv(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def select_setup_strategy(ctx: BootstrapContext, *, requested: str | None = None) -> SetupStrategy:
    if not requested or requested == SetupStrategy.AUTO.value:
        return SetupStrategy.AUTO
    try:
        return SetupStrategy(requested)
    except ValueError as exc:
        raise ValueError(f"Unknown setup strategy: {requested}") from exc


def ensure_system_python(ctx: BootstrapContext) -> Path:
    return ctx.base_python


def ensure_managed_runtime(
    ctx: BootstrapContext,
    *,
    log_info: LogFn | None = None,
    log_warn: LogFn | None = None,
) -> RuntimeStatus:
    override_path = os.environ.get(MANAGED_PYTHON_PATH_ENV)
    if override_path:
        path = Path(override_path).expanduser()
        if path.exists():
            return RuntimeStatus(
                available=True,
                python_path=path,
                detail=f"Using managed Python from {MANAGED_PYTHON_PATH_ENV}.",
            )
        return RuntimeStatus(
            available=False,
            python_path=None,
            detail=f"Managed Python path not found: {path}",
        )

    version = os.environ.get(MANAGED_PYTHON_VERSION_ENV, DEFAULT_MANAGED_PYTHON_VERSION)
    runtime_dir = _managed_runtime_dir(ctx, version)
    existing = _find_python_executable(runtime_dir)
    if existing:
        return RuntimeStatus(
            available=True,
            python_path=existing,
            detail=f"Using cached managed Python {version}.",
        )

    url = os.environ.get(MANAGED_PYTHON_URL_ENV)
    if not url:
        return RuntimeStatus(
            available=False,
            python_path=None,
            detail=(
                "Managed runtime not configured; set "
                f"{MANAGED_PYTHON_URL_ENV} or {MANAGED_PYTHON_PATH_ENV}."
            ),
        )

    if log_info:
        log_info(f"Downloading managed Python {version} runtime")
    try:
        _download_and_extract(url, runtime_dir)
    except Exception as exc:
        if log_warn:
            log_warn(f"Managed runtime download failed: {exc}")
        return RuntimeStatus(
            available=False,
            python_path=None,
            detail="Managed runtime download failed; falling back to system Python.",
        )

    installed = _find_python_executable(runtime_dir)
    if installed:
        return RuntimeStatus(
            available=True,
            python_path=installed,
            detail=f"Installed managed Python {version}.",
        )
    return RuntimeStatus(
        available=False,
        python_path=None,
        detail="Managed runtime installed but python executable was not found.",
    )


def _managed_runtime_dir(ctx: BootstrapContext, version: str) -> Path:
    root = os.environ.get(MANAGED_PYTHON_DIR_ENV)
    base = Path(root).expanduser() if root else ctx.project_root / ".wb" / "runtime"
    return base / version / _platform_tag()


def _platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        machine = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        machine = "arm64" if system == "darwin" else "aarch64"
    if system == "darwin":
        return f"macos-{machine}"
    if system == "windows":
        return f"windows-{machine}"
    return f"linux-{machine}"


def _download_and_extract(url: str, runtime_dir: Path) -> None:
    runtime_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=runtime_dir.parent) as tmp:
        tmp_dir = Path(tmp)
        archive_path = tmp_dir / "runtime.archive"
        _download_file(url, archive_path)
        extract_root = tmp_dir / "extract"
        extract_root.mkdir()
        _extract_archive(archive_path, extract_root)
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir)
        shutil.move(str(extract_root), str(runtime_dir))


def _download_file(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url) as response, dest.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _extract_archive(archive_path: Path, target_dir: Path) -> None:
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            _safe_extract_zip(archive, target_dir)
        return
    with tarfile.open(archive_path, "r:*") as archive:
        _safe_extract_tar(archive, target_dir)


def _safe_extract_tar(archive: tarfile.TarFile, target_dir: Path) -> None:
    root = target_dir.resolve()
    for member in archive.getmembers():
        member_path = (target_dir / member.name).resolve()
        if not str(member_path).startswith(str(root)):
            raise RuntimeError("Unsafe path in archive")
    archive.extractall(path=target_dir)


def _safe_extract_zip(archive: zipfile.ZipFile, target_dir: Path) -> None:
    root = target_dir.resolve()
    for member in archive.infolist():
        member_path = (target_dir / member.filename).resolve()
        if not str(member_path).startswith(str(root)):
            raise RuntimeError("Unsafe path in archive")
    archive.extractall(path=target_dir)


def _find_python_executable(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = [
        root / "python" / "bin" / "python3",
        root / "python" / "bin" / "python",
        root / "bin" / "python3",
        root / "bin" / "python",
        root / "python.exe",
        root / "python" / "python.exe",
        root / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for name in ("python", "python3", "python.exe"):
        for path in root.rglob(name):
            if path.is_file():
                return path
    return None


def create_venv(
    venv_dir: Path,
    base_python: Path,
    *,
    log_info: LogFn | None = None,
    log_warn: LogFn | None = None,
) -> None:
    venv_python = python_in_venv(venv_dir)
    if venv_python.exists():
        if _python_usable(venv_python):
            return
        if log_warn:
            log_warn("Existing virtualenv appears broken; recreating")
        shutil.rmtree(venv_dir)
    if log_info:
        log_info("Creating virtual environment at .venv")
    subprocess.run([str(base_python), "-m", "venv", str(venv_dir)], check=True)


def ensure_pip(
    venv_python: Path,
    *,
    log_info: LogFn | None = None,
    log_error: LogFn | None = None,
) -> bool:
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        if log_info:
            log_info("Bootstrapping pip in virtual environment")
    result = subprocess.run(
        [str(venv_python), "-m", "ensurepip", "--upgrade"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        if log_error:
            log_error(
                "Virtualenv missing pip and ensurepip is unavailable. "
                "On Debian/Ubuntu, install 'python3-venv'. On Windows, repair Python install to enable pip."
            )
        return False
    return True


def upgrade_pip(venv_python: Path) -> None:
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)


def editable_install(
    venv_python: Path,
    project_root: Path,
    *,
    constraints_file: Path | None = None,
    log_info: LogFn | None = None,
    log_warn: LogFn | None = None,
) -> None:
    if constraints_file is None:
        constraints_file = resolve_constraints_file(
            project_root,
            log_info=log_info,
            log_warn=log_warn,
        )
    cmd = [str(venv_python), "-m", "pip", "install", "-e", str(project_root)]
    if constraints_file:
        cmd.extend(["-c", str(constraints_file)])
    subprocess.run(cmd, check=True)


def create_env_file(
    env_file: Path,
    env_example: Path,
    *,
    log_info: LogFn | None = None,
    log_warn: LogFn | None = None,
) -> None:
    if env_file.exists():
        return
    if env_example.exists():
        shutil.copyfile(env_example, env_file)
        if log_info:
            log_info("Created .env from .env.example")
    else:
        if log_warn:
            log_warn(".env.example not found; skipping .env creation")


def resolve_constraints_file(
    project_root: Path,
    *,
    log_info: LogFn | None = None,
    log_warn: LogFn | None = None,
) -> Path | None:
    override = os.environ.get(PIP_CONSTRAINTS_ENV)
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            path = project_root / path
        if path.exists():
            if log_info:
                log_info(f"Using pip constraints from {path}")
            return path
        if log_warn:
            log_warn(f"Constraints file not found: {path}")
        return None
    for name in DEFAULT_CONSTRAINTS_FILES:
        candidate = project_root / name
        if candidate.exists():
            if log_info:
                log_info(f"Using pip constraints from {candidate}")
            return candidate
    return None


def validate_system_python(
    ctx: BootstrapContext,
    *,
    log_error: LogFn | None = None,
    log_warn: LogFn | None = None,
) -> bool:
    version = _get_python_version(ctx.base_python)
    if version is None:
        if log_error:
            log_error("Unable to run system Python. Install Python 3.10+ or configure a managed runtime.")
        return False
    if version < MIN_PYTHON_VERSION:
        if log_error:
            log_error(
                f"Python {MIN_PYTHON_TEXT}+ is required. Install a newer Python or configure "
                f"{MANAGED_PYTHON_URL_ENV}/{MANAGED_PYTHON_PATH_ENV} to use a managed runtime."
            )
        return False
    if not _python_can_import(ctx.base_python, "venv"):
        if log_error:
            log_error(
                "System Python is missing the venv module. On Debian/Ubuntu, install 'python3-venv'."
            )
        return False
    if not _python_can_import(ctx.base_python, "ensurepip") and log_warn:
        log_warn(
            "System Python is missing ensurepip; dependency installs may fail. "
            "On Debian/Ubuntu, install 'python3-venv'."
        )
    return True


def _python_usable(python_path: Path) -> bool:
    try:
        subprocess.run(
            [str(python_path), "-V"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _get_python_version(python_path: Path) -> tuple[int, int, int] | None:
    if python_path.resolve() == Path(sys.executable).resolve():
        return tuple(sys.version_info[:3])
    code = "import json, sys; print(json.dumps(list(sys.version_info[:3])))"
    try:
        result = subprocess.run(
            [str(python_path), "-c", code],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None
    try:
        data = result.stdout.strip()
        version = json.loads(data)
        return tuple(int(part) for part in version[:3])
    except Exception:
        return None


def _python_can_import(python_path: Path, module: str) -> bool:
    code = f"import {module}"
    try:
        subprocess.run(
            [str(python_path), "-c", code],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False
