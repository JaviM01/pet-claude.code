# -*- coding: utf-8 -*-
"""
Installer for Claude Code Mascot.

Adds Notification and Stop hooks to ~/.claude/settings.json
pointing to mascota.py in this directory.

Usage:
    python install.py
"""

import json
import os
import pathlib
import platform
import sys


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


def build_commands(python: str, script: pathlib.Path):
    """Returns (notification_cmd, stop_cmd) for the current OS."""
    p = str(python).replace("\\", "\\\\")
    s = str(script).replace("\\", "\\\\")

    if platform.system() == "Windows":
        notification = f'start "" "{p}" "{s}" notification'
        stop = f'start "" "{p}" "{s}" stop'
    else:
        # & runs the process in background so the hook doesn't block Claude
        notification = f'"{python}" "{script}" notification &'
        stop = f'"{python}" "{script}" stop &'

    return notification, stop


def main():
    script = pathlib.Path(__file__).parent.resolve() / "mascota.py"
    settings_path = pathlib.Path.home() / ".claude" / "settings.json"

    if not script.exists():
        print(f"ERROR: mascota.py not found at {script}")
        sys.exit(1)

    python = find_pythonw()
    print(f"Python  : {python}")
    print(f"Script  : {script}")
    print(f"Settings: {settings_path}")

    # Load existing settings or start fresh
    settings = {}
    if settings_path.exists():
        try:
            with open(settings_path, encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("WARNING: settings.json has invalid JSON — starting fresh hooks section.")

    notification_cmd, stop_cmd = build_commands(python, script)

    settings.setdefault("hooks", {})
    settings["hooks"]["Notification"] = [
        {"hooks": [{"type": "command", "command": notification_cmd}]}
    ]
    settings["hooks"]["Stop"] = [
        {"hooks": [{"type": "command", "command": stop_cmd}]}
    ]

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print("\nDone! Hooks installed successfully.")
    print("Restart Claude Code (or run /hooks) to activate the mascot.")


if __name__ == "__main__":
    main()
