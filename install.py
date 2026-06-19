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

    # Show notification overlay — stays until dismissed
    settings["hooks"]["Notification"] = [
        {"hooks": [{"type": "command", "command": build_command(python, script, "notification")}]}
    ]
    # Show completion overlay — auto-closes
    settings["hooks"]["Stop"] = [
        {"hooks": [{"type": "command", "command": build_command(python, script, "stop")}]}
    ]
    # Dismiss notification overlay when Claude finishes using a tool
    # (fires after user accepts/denies a permission prompt)
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


if __name__ == "__main__":
    main()
