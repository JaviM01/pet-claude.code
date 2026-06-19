# -*- coding: utf-8 -*-
"""
Installer for Claude Code Mascot.

Adds Notification, Stop, and PostToolUse hooks to ~/.claude/settings.json
pointing to mascota.py in this directory.

Usage:
    python install.py
"""

import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys


def ensure_tkinter():
    """Check tkinter is available; install it automatically if not."""
    try:
        import tkinter  # noqa: F401
        return True
    except ImportError:
        pass

    system = platform.system()
    print("tkinter not found — attempting automatic installation...")

    if system == "Darwin":
        brew = shutil.which("brew")
        if not brew:
            print("ERROR: Homebrew not found. Install it from https://brew.sh, then run:")
            py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
            print(f"  brew install python-tk@{py_ver}")
            return False

        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        pkg = f"python-tk@{py_ver}"
        print(f"Running: brew install {pkg}")
        result = subprocess.run([brew, "install", pkg])
        if result.returncode != 0:
            print(f"ERROR: brew install failed. Try manually: brew install {pkg}")
            return False
        print(f"[OK] {pkg} installed.")
        return True

    if system == "Linux":
        if shutil.which("apt-get"):
            print("Running: sudo apt-get install -y python3-tk")
            result = subprocess.run(["sudo", "apt-get", "install", "-y", "python3-tk"])
            if result.returncode == 0:
                print("[OK] python3-tk installed.")
                return True
        elif shutil.which("dnf"):
            print("Running: sudo dnf install -y python3-tkinter")
            result = subprocess.run(["sudo", "dnf", "install", "-y", "python3-tkinter"])
            if result.returncode == 0:
                print("[OK] python3-tkinter installed.")
                return True
        print("ERROR: Could not install tkinter automatically.")
        print("Install it manually for your distro (e.g. sudo apt install python3-tk).")
        return False

    if system == "Windows":
        print("ERROR: tkinter not found. Reinstall Python from https://python.org")
        print("and make sure 'tcl/tk and IDLE' is checked during setup.")
        return False

    return False


def find_pythonw():
    """
    Returns the best Python executable for launching mascota.py silently.
    On Windows: prefers pythonw.exe (no console window).
    On macOS/Linux: uses the current interpreter.
    """
    if platform.system() == "Windows":
        here = pathlib.Path(sys.executable).parent
        pythonw = here / "pythonw.exe"
        return str(pythonw) if pythonw.exists() else sys.executable
    return sys.executable


def build_command(python: str, script: pathlib.Path, event: str) -> str:
    """Returns the hook command string for the given event."""
    p = str(python).replace("\\", "\\\\")
    s = str(script).replace("\\", "\\\\")

    if platform.system() == "Windows":
        return f'start "" "{p}" "{s}" {event}'
    else:
        return f'"{python}" "{script}" {event} &'


def main():
    script = pathlib.Path(__file__).parent.resolve() / "mascota.py"
    settings_path = pathlib.Path.home() / ".claude" / "settings.json"

    if not script.exists():
        print(f"ERROR: mascota.py not found at {script}")
        sys.exit(1)

    if not ensure_tkinter():
        sys.exit(1)

    python = find_pythonw()
    print(f"Python  : {python}")
    print(f"Script  : {script}")
    print(f"Settings: {settings_path}")

    settings = {}
    if settings_path.exists():
        try:
            with open(settings_path, encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("WARNING: settings.json has invalid JSON — starting fresh hooks section.")

    settings.setdefault("hooks", {})

    settings["hooks"]["Notification"] = [
        {"hooks": [{"type": "command", "command": build_command(python, script, "notification")}]}
    ]
    settings["hooks"]["Stop"] = [
        {"hooks": [{"type": "command", "command": build_command(python, script, "stop")}]}
    ]
    settings["hooks"]["PostToolUse"] = [
        {"hooks": [{"type": "command", "command": build_command(python, script, "dismiss")}]}
    ]

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print("\nDone! Hooks installed:")
    print("  Notification -> show notification overlay (waits for user)")
    print("  Stop         -> show completion overlay (auto-closes)")
    print("  PostToolUse  -> dismiss notification overlay automatically")
    print("\nRestart Claude Code (or run /hooks) to activate.")

    if platform.system() == "Darwin":
        print("\nmacOS note: if the window doesn't appear, grant Accessibility permission")
        print("to Terminal in System Settings > Privacy & Security > Accessibility.")


if __name__ == "__main__":
    main()
