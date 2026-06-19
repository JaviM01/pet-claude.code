# -*- coding: utf-8 -*-
"""
Claude Code Mascot - animated overlay triggered by Claude Code hooks.

Shows a borderless, always-on-top window in the bottom-right corner with
an animated GIF (or emoji fallback) that auto-closes after a few seconds.

Usage:
    python mascota.py <event> ["optional message"]

Events:
    notification  -> Claude needs permission / attention
    stop          -> Claude finished the task
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
    BG_CANVAS = "#ff00ff"          # magenta -> transparent via -transparentcolor
    FUENTE_EMOJI = ("Segoe UI Emoji", 38)
    FUENTE_UI_BOLD = ("Segoe UI", 13, "bold")
    FUENTE_UI = ("Segoe UI", 10)
    OFFSET_Y = 64                  # taskbar height
elif SISTEMA == "Darwin":
    BG_CANVAS = "#1a1a2e"          # dark bg (no per-pixel transparency on macOS)
    FUENTE_EMOJI = ("Apple Color Emoji", 38)
    FUENTE_UI_BOLD = ("Helvetica Neue", 13, "bold")
    FUENTE_UI = ("Helvetica Neue", 10)
    OFFSET_Y = 80                  # dock height
else:
    BG_CANVAS = "#1a1a2e"
    FUENTE_EMOJI = ("Noto Color Emoji", 38)
    FUENTE_UI_BOLD = ("DejaVu Sans", 13, "bold")
    FUENTE_UI = ("DejaVu Sans", 10)
    OFFSET_Y = 64

# ---------------------------------------------------------------------------
# GIF paths — relative to this script so the repo is self-contained.
# Put your GIFs in the gifs/ folder next to mascota.py.
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

EVENTOS = {
    "notification": {
        "gif": os.path.join(SCRIPT_DIR, "gifs", "notification.gif"),
        "frames": ["🙋", "👋"],
        "titulo": "Claude needs you",
        "mensaje": "May I continue?",
        "color": "#2563eb",
    },
    "stop": {
        "gif": os.path.join(SCRIPT_DIR, "gifs", "stop.gif"),
        "frames": ["🎉", "🥳"],
        "titulo": "Done!",
        "mensaje": "Task finished",
        "color": "#16a34a",
    },
    "_default": {
        "gif": None,
        "frames": ["🤖", "✨"],
        "titulo": "Claude Code",
        "mensaje": "",
        "color": "#7c3aed",
    },
}

DURACION_MS = 3800
FRAME_MS = 80
MAX_LADO = 280


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


def mostrar_gif(root, cfg):
    frames = cargar_gif(cfg["gif"]) if cfg.get("gif") else []
    if not frames:
        return False

    w, h = frames[0].width(), frames[0].height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = sw - w - 24, sh - h - OFFSET_Y
    root.geometry(f"{w}x{h}+{x}+{y}")

    canvas = tk.Canvas(root, width=w, height=h, bg=BG_CANVAS, highlightthickness=0)
    canvas.pack()
    canvas._frames = frames
    img_id = canvas.create_image(w // 2, h // 2, image=frames[0])
    canvas.bind("<Button-1>", lambda e: root.destroy())

    estado = {"frame": 0, "alpha": 0.0, "cerrando": False}

    def animar_frame():
        estado["frame"] = (estado["frame"] + 1) % len(frames)
        canvas.itemconfig(img_id, image=frames[estado["frame"]])
        try:
            root.after(FRAME_MS, animar_frame)
        except tk.TclError:
            pass

    def fade():
        if not estado["cerrando"] and estado["alpha"] < 0.99:
            estado["alpha"] = min(0.99, estado["alpha"] + 0.08)
            root.attributes("-alpha", estado["alpha"])
        if estado["cerrando"]:
            estado["alpha"] -= 0.07
            if estado["alpha"] <= 0:
                root.destroy()
                return
            root.attributes("-alpha", estado["alpha"])
        try:
            root.after(16, fade)
        except tk.TclError:
            pass

    root.after(FRAME_MS, animar_frame)
    root.after(16, fade)
    root.after(DURACION_MS, lambda: estado.__setitem__("cerrando", True))
    root.after(DURACION_MS + 1500, root.destroy)
    return True


def mostrar_emoji(root, cfg, mensaje):
    ANCHO, ALTO = 300, 120
    root.attributes("-alpha", 0.0)
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
    canvas.bind("<Button-1>", lambda e: root.destroy())

    estado = {"t": 0, "alpha": 0.0, "cerrando": False}

    def animar():
        estado["t"] += 1
        t = estado["t"]
        canvas.coords(emoji_id, 56, base_y + math.sin(t / 6.0) * 8)
        canvas.itemconfig(emoji_id, text=cfg["frames"][(t // 25) % len(cfg["frames"])])
        if not estado["cerrando"] and estado["alpha"] < 0.97:
            estado["alpha"] = min(0.97, estado["alpha"] + 0.08)
            root.attributes("-alpha", estado["alpha"])
        if estado["cerrando"]:
            estado["alpha"] -= 0.07
            if estado["alpha"] <= 0:
                root.destroy()
                return
            root.attributes("-alpha", estado["alpha"])
        try:
            root.after(16, animar)
        except tk.TclError:
            pass

    root.after(16, animar)
    root.after(DURACION_MS, lambda: estado.__setitem__("cerrando", True))
    root.after(DURACION_MS + 1500, root.destroy)


def main():
    evento = sys.argv[1] if len(sys.argv) > 1 else "_default"
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

    # Per-pixel transparency: only works on Windows
    if SISTEMA == "Windows":
        try:
            root.attributes("-transparentcolor", BG_CANVAS)
        except tk.TclError:
            pass

    if not mostrar_gif(root, cfg):
        mostrar_emoji(root, cfg, mensaje)

    root.mainloop()


if __name__ == "__main__":
    main()
