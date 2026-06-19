# Claude Code Mascot 🤖

An animated overlay that appears whenever Claude Code needs your attention or finishes a task. Drop your own GIFs in the `gifs/` folder and it just works.

![demo placeholder](gifs/preview.gif)

## How it works

Claude Code supports [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — shell commands triggered by events. This project hooks into two of them:

| Event | When it fires | Default GIF |
|-------|--------------|-------------|
| `Notification` | Claude asks for permission | `gifs/notification.gif` |
| `Stop` | Claude finishes a task | `gifs/stop.gif` |

The overlay appears in the **bottom-right corner**, fades in, stays for ~4 seconds, then fades out. Click it to dismiss early.

**Works on Windows and macOS.** On Windows the window is fully transparent (GIF floats on screen). On macOS it uses a dark semi-transparent background.

## Requirements

- Python 3.8+ with `tkinter` (included in the standard library)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

### Check tkinter

```bash
python3 -c "import tkinter; print('tkinter OK')"
```

If it fails on macOS, install Python from [python.org](https://python.org) (Homebrew's Python sometimes ships without tkinter).

## Installation

1. **Clone the repo**

```bash
git clone https://github.com/YOUR_USERNAME/claude-mascota
cd claude-mascota
```

2. **Add your GIFs**

```
gifs/
├── notification.gif   ← shown when Claude needs permission
└── stop.gif           ← shown when Claude finishes
```

The GIFs are gitignored — bring your own! Any animated GIF works; large ones are auto-scaled to fit 280px.

3. **Run the installer**

```bash
python install.py
```

This writes the hooks into `~/.claude/settings.json` automatically.

4. **Restart Claude Code** (or run `/hooks` inside it)

That's it — the mascot is live.

## Uninstall

Remove the `Notification` and `Stop` entries from `~/.claude/settings.json`, or delete the hooks section entirely.

## Customization

All tweakable constants are at the top of `mascota.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `DURACION_MS` | `3800` | How long the overlay stays visible (ms) |
| `FRAME_MS` | `80` | GIF animation speed (ms per frame) |
| `MAX_LADO` | `280` | Max GIF size in pixels (auto-scales larger GIFs) |

To add more events (e.g. `PreToolUse`), add an entry to the `EVENTOS` dict and add the corresponding hook via the installer or directly in `settings.json`.

## Emoji fallback

If a GIF file is missing or can't be loaded, the mascot falls back to an animated emoji overlay. No crash, no errors.

## License

MIT
