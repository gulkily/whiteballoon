#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
import socket


# -------- Logging helpers --------

def _supports_color() -> bool:
    if platform.system() == "Windows":
        return False  # keep simple; wrappers provide color
    return sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _supports_color() else text


def info(msg: str) -> None:
    print(_c("0;34", f"[INFO] {msg}"))


def warn(msg: str) -> None:
    print(_c("1;33", f"[WARN] {msg}"))


def error(msg: str) -> None:
    print(_c("0;31", f"[ERROR] {msg}"), file=sys.stderr)


# -------- Paths and execution helpers --------

SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / ".venv"
DEV_TOOL = SCRIPT_DIR / "tools" / "dev.py"


def python_in_venv() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run(argv: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(argv, check=check)


# -------- Environment bootstrap --------

def create_venv() -> None:
    if python_in_venv().exists():
        return
    info("Creating virtual environment at .venv")
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)


def ensure_pip(venv_python: Path) -> None:
    try:
        subprocess.run([str(venv_python), "-m", "pip", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception:
        info("Bootstrapping pip in virtual environment")
    # Try ensurepip
    result = subprocess.run([str(venv_python), "-m", "ensurepip", "--upgrade"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        error(
            "Virtualenv missing pip and ensurepip is unavailable. On Debian/Ubuntu, install 'python3-venv'. On Windows, repair Python install to enable pip."
        )
        sys.exit(1)


def upgrade_pip(venv_python: Path) -> None:
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)


def editable_install(venv_python: Path) -> None:
    subprocess.run([str(venv_python), "-m", "pip", "install", "-e", str(SCRIPT_DIR)], check=True)


def create_env_file() -> None:
    env_file = SCRIPT_DIR / ".env"
    env_example = SCRIPT_DIR / ".env.example"
    if env_file.exists():
        return
    if env_example.exists():
        shutil.copyfile(env_example, env_file)
        info("Created .env from .env.example")
    else:
        warn(".env.example not found; skipping .env creation")


# -------- Dev tool integration --------

def ensure_cli_ready(python_exe: Path) -> bool:
    code = (
        "try:\n"
        "    import fastapi\n"
        "    import click\n"
        "except Exception:\n"
        "    raise SystemExit(1)\n"
    )
    result = subprocess.run([str(python_exe), "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def dev_invoke(venv_python: Path, *args: str) -> int:
    proc = subprocess.run([str(venv_python), str(DEV_TOOL), *args])
    return proc.returncode


def cmd_hub(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="wb hub", description="Manage the sync hub service")
    parser.add_argument("action", choices=["serve"], nargs="?", default="serve")
    parser.add_argument("--config", dest="config", default=None, help="Path to hub config (WB_HUB_CONFIG)")
    parser.add_argument("--host", dest="host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", dest="port", type=int, default=9100, help="Port to bind")
    parser.add_argument("--reload", dest="reload", action="store_true", help="Enable autoreload (dev only)")
    ns = parser.parse_args(args)

    vpy = python_in_venv()
    if not vpy.exists():
        warn("Virtualenv missing. Run './wb setup' first.")
        return 1
    env = os.environ.copy()
    if ns.config:
        env["WB_HUB_CONFIG"] = ns.config
    cmd = [
        str(vpy),
        "-m",
        "uvicorn",
        "app.hub:hub_app",
        "--host",
        ns.host,
        "--port",
        str(ns.port),
    ]
    if ns.reload:
        cmd.append("--reload")
    info(f"Starting hub on {ns.host}:{ns.port}")
    return subprocess.run(cmd, env=env).returncode


# -------- CLI handlers --------

def cmd_setup(_args: argparse.Namespace) -> int:
    create_venv()
    vpy = python_in_venv()
    ensure_pip(vpy)
    info("Installing project dependencies")
    upgrade_pip(vpy)
    editable_install(vpy)
    create_env_file()
    info("Initializing database")
    rc = dev_invoke(vpy, "init-db")
    if rc != 0:
        error("Database initialization failed")
        return rc
    info("Setup complete")
    return 0


def cmd_known(known_cmd: str, passthrough: list[str]) -> int:
    vpy = python_in_venv()
    if not ensure_cli_ready(vpy):
        warn("Dependencies missing. Run './wb setup' first.")
        print()
        print_help()
        return 1
    return dev_invoke(vpy, known_cmd, *passthrough)


def _parse_host_port(args: list[str]) -> tuple[str, int]:
    host = "127.0.0.1"
    port = 8000
    it = iter(range(len(args)))
    for i in it:
        a = args[i]
        if a == "--host" and i + 1 < len(args):
            host = args[i + 1]
            next(it, None)
        elif a.startswith("--host="):
            host = a.split("=", 1)[1]
        elif a == "--port" and i + 1 < len(args):
            try:
                port = int(args[i + 1])
            except ValueError:
                pass
            next(it, None)
        elif a.startswith("--port="):
            try:
                port = int(a.split("=", 1)[1])
            except ValueError:
                pass
    return host, port


def _port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def preflight_runserver(passthrough: list[str]) -> bool:
    host, port = _parse_host_port(passthrough)
    if _port_available(host, port):
        return True
    warn(f"Address already in use: {host}:{port}")
    print("Try one of the following:")
    print(f"  - Choose a different port: wb runserver --port {port + 1}")
    if platform.system() == "Windows":
        print(f"  - Find process: netstat -ano ^| findstr :{port}")
        print("  - Then terminate via Task Manager or: taskkill /PID <pid> /F")
    else:
        print(f"  - Find process: lsof -i :{port} -sTCP:LISTEN")
        print(f"  - Kill process: fuser -k {port}/tcp")
    return False


def print_help() -> None:
    print("WhiteBalloon CLI Wrapper")
    print("Usage: wb <command> [options]")
    print()
    print("Core commands:")
    print("  setup                 Create virtualenv, install dependencies, and initialize the database")
    print("  runserver [--opts]    Start the development server")
    print("  init-db               Initialize the SQLite database")
    print("  create-admin USER     Promote a user to admin")
    print("  create-invite [opts]  Generate invite tokens")
    print("  sync <command> [opts] Manual sync utilities (export/import)")
    print("  hub serve [opts]      Run the sync hub (uvicorn)")
    print("  version               Display CLI version info")
    print("  help                  Show this help message")
    print()
    print("Any other arguments are forwarded to the underlying Click CLI in tools/dev.py.")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("help")
    subparsers.add_parser("version")
    subparsers.add_parser("setup")
    subparsers.add_parser("runserver")
    subparsers.add_parser("init-db")
    subparsers.add_parser("create-admin")
    subparsers.add_parser("create-invite")
    subparsers.add_parser("sync")
    subparsers.add_parser("hub")

    # Parse only the command; leave the rest as passthrough
    known, passthrough = (argv[:1], argv[1:]) if argv else ([], [])
    ns, _ = parser.parse_known_args(known)

    if not argv or ns.command in (None, "help"):
        print_help()
        return 0

    if ns.command == "version":
        print("WhiteBalloon CLI 0.1.0")
        return 0

    if ns.command == "setup":
        return cmd_setup(ns)

    if ns.command == "hub":
        return cmd_hub(passthrough)

    # Known commands path
    if ns.command in {"runserver", "init-db", "create-admin", "create-invite", "sync"}:
        if ns.command == "sync":
            if not passthrough:
                passthrough = ["--help"]
            elif passthrough[0] == "help":
                passthrough = ["--help", *passthrough[1:]]
        if ns.command == "runserver" and not preflight_runserver(passthrough):
            return 1
        rc = cmd_known(ns.command, passthrough)
        if rc != 0 and ns.command not in {"runserver", "sync"}:
            warn("Command failed. Run './wb setup' first if not done.")
            print()
            print_help()
        return rc

    # Default passthrough to dev tool
    vpy = python_in_venv()
    if not ensure_cli_ready(vpy):
        warn("Dependencies missing. Run './wb setup' first.")
        print()
        print_help()
        return 1
    rc = dev_invoke(vpy, *argv)
    if rc != 0:
        warn(f"Command '{argv[0]}' not recognized or failed.")
        print()
        print_help()
    return rc


if __name__ == "__main__":
    sys.exit(main())
