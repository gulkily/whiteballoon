from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable
import platform
import shutil
import subprocess
import sys

LogFn = Callable[[str], None]


class SetupStrategy(Enum):
    AUTO = "auto"
    MANAGED = "managed"
    SYSTEM = "system"


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
        return SetupStrategy.SYSTEM
    try:
        return SetupStrategy(requested)
    except ValueError as exc:
        raise ValueError(f"Unknown setup strategy: {requested}") from exc


def ensure_system_python(ctx: BootstrapContext) -> Path:
    return ctx.base_python


def ensure_managed_runtime(ctx: BootstrapContext) -> RuntimeStatus:
    return RuntimeStatus(
        available=False,
        python_path=None,
        detail="Managed runtime not configured yet; falling back to system Python.",
    )


def create_venv(venv_dir: Path, base_python: Path, *, log_info: LogFn | None = None) -> None:
    if python_in_venv(venv_dir).exists():
        return
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


def editable_install(venv_python: Path, project_root: Path) -> None:
    subprocess.run([str(venv_python), "-m", "pip", "install", "-e", str(project_root)], check=True)


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
