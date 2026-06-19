# -*- coding: utf-8 -*-
"""
Claude Code Mascot - animated overlay triggered by Claude Code hooks.

Shows a borderless, always-on-top window in the bottom-right corner with
an animated GIF (or emoji fallback).

Behaviour by event:
  notification  - stays visible (breathing pulse) until dismissed
  stop          - auto-closes after a few seconds
  dismiss       - silently closes any open notification overlay (no window)

Dismiss mechanism: notification creates a lock file; any subsequent event
(PostToolUse, Stop, or a new Notification) deletes it. The overlay polls
the lock file every 300 ms and fades out when it disappears.

Usage:
    python mascota.py <event> ["optional message"]
"""

import os
import sys
import json
import math
import platform
import tkinter as tk

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
SISTEMA = platform.system()  # 'Windows', 'Darwin', 'Linux'

if SISTEMA == "Windows":
    BG_CANVAS = "#ff00ff"
    FUENTE_EMOJI = ("Segoe UI Emoji", 38)
    FUENTE_UI_BOLD = ("Segoe UI", 13, "bold")
    FUENTE_UI = ("Segoe UI", 10)
    OFFSET_Y = 64
elif SISTEMA == "Darwin":
    BG_CANVAS = "#1a1a2e"
    FUENTE_EMOJI = ("Apple Color Emoji", 38)
    FUENTE_UI_BOLD = ("Helvetica Neue", 13, "bold")
    FUENTE_UI = ("Helvetica Neue", 10)
    OFFSET_Y = 80
else:
    BG_CANVAS = "#1a1a2e"
    FUENTE_EMOJI = ("Noto Color Emoji", 38)
    FUENTE_UI_BOLD = ("DejaVu Sans", 13, "bold")
    FUENTE_UI = ("DejaVu Sans", 10)
    OFFSET_Y = 64

# ---------------------------------------------------------------------------
# Lock file — used to signal the notification overlay to close
# ---------------------------------------------------------------------------
LOCK_FILE = os.path.join(os.path.expanduser("~"), ".claude", "mascota", "notification.lock")


def crear_lock():
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    open(LOCK_FILE, "w").close()


def borrar_lock():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# GIF paths — relative to this script
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

EVENTOS = {
    "notification": {
        "gif": os.path.join(SCRIPT_DIR, "gifs", "notification.gif"),
        "frames": ["🙋", "👋"],
        "titulo": "Claude needs you",
        "mensaje": "May I continue?",
        "color": "#2563eb",
        "auto_cerrar": False,
    },
    "stop": {
        "gif": os.path.join(SCRIPT_DIR, "gifs", "stop.gif"),
        "frames": ["🎉", "🥳"],
        "titulo": "Done!",
        "mensaje": "Task finished",
        "color": "#16a34a",
        "auto_cerrar": True,
    },
    "_default": {
        "gif": None,
        "frames": ["🤖", "✨"],
        "titulo": "Claude Code",
        "mensaje": "",
        "color": "#7c3aed",
        "auto_cerrar": True,
    },
}

DURACION_MS = 3800
FRAME_MS    = 80
MAX_LADO    = 280


def leer_payload():
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw and raw.strip() else {}
    except Exception:
        return {}


def cargar_gif(path):
    frames = []
    i = 0
    while True:
        try:
            frames.append(tk.PhotoImage(file=path, format=f"gif -index {i}"))
        except tk.TclError:
            break
        i += 1
    if not frames:
        return frames
    lado = max(frames[0].width(), frames[0].height())
    if lado > MAX_LADO:
        factor = (lado + MAX_LADO - 1) // MAX_LADO
        frames = [f.subsample(factor, factor) for f in frames]
    return frames


def _watch_sentinel(root, cerrar):
    """Poll every 300 ms — if lock file is gone, close the overlay."""
    if not os.path.exists(LOCK_FILE):
        cerrar()
        return
    try:
        root.after(300, lambda: _watch_sentinel(root, cerrar))
    except tk.TclError:
        pass


def _ciclo_alpha(root, cfg, on_tick=None):
    """
    State machine: fade_in -> pulse (persistent) or idle (auto-close) -> fade_out
    Returns cerrar(), a callable that triggers the fade_out from any source.
    """
    auto_cerrar = cfg.get("auto_cerrar", True)
    estado = {"fase": "fade_in", "alpha": 0.0, "t": 0}

    def cerrar(*_):
        if estado["fase"] != "fade_out":
            estado["fase"] = "fade_out"

    def ciclo():
        try:
            fase = estado["fase"]
            if fase == "fade_in":
                estado["alpha"] = min(0.99, estado["alpha"] + 0.08)
                root.attributes("-alpha", estado["alpha"])
                if estado["alpha"] >= 0.99:
                    estado["fase"] = "idle" if auto_cerrar else "pulse"

            elif fase == "pulse":
                estado["t"] += 1
                a = 0.82 + 0.17 * math.sin(estado["t"] / 18.0)
                root.attributes("-alpha", a)

            elif fase == "idle":
                pass

            elif fase == "fade_out":
                estado["alpha"] = float(root.attributes("-alpha"))
                estado["alpha"] -= 0.08
                if estado["alpha"] <= 0:
                    root.destroy()
                    return
                root.attributes("-alpha", max(0.0, estado["alpha"]))

            if on_tick:
                on_tick(estado)

            root.after(16, ciclo)
        except tk.TclError:
            pass

    root.after(16, ciclo)

    if auto_cerrar:
        root.after(DURACION_MS, cerrar)
        root.after(DURACION_MS + 1500,
                   lambda: root.destroy() if root.winfo_exists() else None)

    return cerrar


def mostrar_gif(root, cfg):
    """Returns cerrar callable, or None if GIF could not be loaded."""
    frames = cargar_gif(cfg["gif"]) if cfg.get("gif") else []
    if not frames:
        return None

    w, h = frames[0].width(), frames[0].height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = sw - w - 24, sh - h - OFFSET_Y
    root.geometry(f"{w}x{h}+{x}+{y}")

    canvas = tk.Canvas(root, width=w, height=h, bg=BG_CANVAS, highlightthickness=0)
    canvas.pack()
    canvas._frames = frames
    img_id = canvas.create_image(w // 2, h // 2, image=frames[0])

    frame_idx = [0]

    def animar_frame():
        frame_idx[0] = (frame_idx[0] + 1) % len(frames)
        canvas.itemconfig(img_id, image=frames[frame_idx[0]])
        try:
            root.after(FRAME_MS, animar_frame)
        except tk.TclError:
            pass

    root.after(FRAME_MS, animar_frame)

    cerrar = _ciclo_alpha(root, cfg)
    canvas.bind("<Button-1>", cerrar)
    root.bind("<Escape>", cerrar)
    return cerrar


def mostrar_emoji(root, cfg, mensaje):
    """Always succeeds; returns cerrar callable."""
    ANCHO, ALTO = 300, 120
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = sw - ANCHO - 24, sh - ALTO - OFFSET_Y
    root.geometry(f"{ANCHO}x{ALTO}+{x}+{y}")

    canvas = tk.Canvas(root, width=ANCHO, height=ALTO, bg=BG_CANVAS, highlightthickness=0)
    canvas.pack()

    pad = 8
    canvas.create_rectangle(pad + 12, pad, ANCHO - pad - 12, ALTO - pad,
                             fill=cfg["color"], outline="")
    canvas.create_rectangle(pad, pad + 12, ANCHO - pad, ALTO - pad - 12,
                             fill=cfg["color"], outline="")
    for cx, cy in [(pad + 12, pad + 12), (ANCHO - pad - 12, pad + 12),
                   (pad + 12, ALTO - pad - 12), (ANCHO - pad - 12, ALTO - pad - 12)]:
        canvas.create_oval(cx - 12, cy - 12, cx + 12, cy + 12,
                            fill=cfg["color"], outline="")

    base_y = ALTO // 2
    emoji_id = canvas.create_text(56, base_y, text=cfg["frames"][0], font=FUENTE_EMOJI)
    canvas.create_text(104, base_y - 16, text=cfg["titulo"], anchor="w",
                       fill="white", font=FUENTE_UI_BOLD)
    canvas.create_text(104, base_y + 12, text=mensaje, anchor="w",
                       fill="white", font=FUENTE_UI)

    t = [0]

    def on_tick(_estado):
        t[0] += 1
        canvas.coords(emoji_id, 56, base_y + math.sin(t[0] / 6.0) * 8)
        canvas.itemconfig(emoji_id, text=cfg["frames"][(t[0] // 25) % len(cfg["frames"])])

    cerrar = _ciclo_alpha(root, cfg, on_tick=on_tick)
    canvas.bind("<Button-1>", cerrar)
    root.bind("<Escape>", cerrar)
    return cerrar


def main():
    evento = sys.argv[1] if len(sys.argv) > 1 else "_default"

    # Every event (except notification itself) dismisses any open notification overlay.
    # 'dismiss' is a no-window command used by the PostToolUse hook.
    if evento != "notification":
        borrar_lock()
    if evento == "dismiss":
        sys.exit(0)

    cfg = EVENTOS.get(evento, EVENTOS["_default"])

    payload = leer_payload()
    mensaje = ""
    if len(sys.argv) > 2:
        mensaje = sys.argv[2]
    elif isinstance(payload, dict):
        mensaje = payload.get("message") or cfg["mensaje"]
    if not mensaje:
        mensaje = cfg["mensaje"]

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.0)
    root.configure(bg=BG_CANVAS)

    if SISTEMA == "Windows":
        try:
            root.attributes("-transparentcolor", BG_CANVAS)
        except tk.TclError:
            pass

    cerrar = mostrar_gif(root, cfg) or mostrar_emoji(root, cfg, mensaje)

    if not cfg.get("auto_cerrar", True):
        crear_lock()
        # Delete lock when overlay closes for any reason (click, ESC, or sentinel)
        root.bind("<Destroy>", lambda e: borrar_lock())
        _watch_sentinel(root, cerrar)

    root.mainloop()


if __name__ == "__main__":
    main()
