#!/usr/bin/env python3
"""BMO Face Showcase — framebuffer directo, sin X11 ni Wayland."""
import time, os, sys
from PIL import Image
import numpy as np

FACES = "/home/mch/Projects/be-more-agent/faces"

STATES = [
    # Estados funcionales (sesión anterior)
    ("warmup",    "🔥 WARMUP"),
    ("idle",      "😴 IDLE"),
    ("listening", "👂 LISTENING"),
    ("thinking",  "🧠 THINKING"),
    ("speaking",  "🗣️ SPEAKING"),
    ("error",     "⚠️ ERROR"),
    ("capturing", "📷 CAPTURING"),
    # Caras nuevas de ayer (02:57)
    ("blink",     "😉 BLINK"),
    ("corazon",   "❤️ CORAZÓN"),
    ("enojado",   "😠 ENOJADO"),
    ("feliz",     "😊 FELIZ"),
    ("shrek_cat", "😸 SHREK CAT"),
    ("sorprendido","😮 SORPRENDIDO"),
    ("sospechoso", "🤨 SOSPECHOSO"),
    # Caras nuevas generadas hoy
    ("triste",    "😢 TRISTE"),
    ("guino",     "😉 GUIÑO"),
    ("fiesta",    "🎉 FIESTA"),
    ("beso",      "😘 BESO"),
    ("dormido",   "😴 DORMIDO"),
    ("confundido","🤔 CONFUNDIDO"),
    ("asustado",  "😨 ASUSTADO"),
    ("llorando",  "😭 LLORANDO"),
    ("sonrisa",   "🙂 SONRISA"),
    ("frio",      "🥶 FRÍO"),
    ("timido",    "🥺 TÍMIDO"),
    ("hambre",    "🤤 HAMBRE"),
    ("risueno",   "😂 RISUEÑO"),
    ("bostezo",   "🥱 BOSTEZO"),
]

FB = "/dev/fb0"
W, H = 800, 480

def load_frames(folder):
    path = os.path.join(FACES, folder)
    pngs = sorted([f for f in os.listdir(path) if f.endswith(".png")])
    frames = []
    for p in pngs:
        img = Image.open(os.path.join(path, p)).convert("RGBA").resize((W, H))
        arr = np.array(img)
        bgra = np.zeros((H, W, 4), dtype=np.uint8)
        bgra[:,:,0] = arr[:,:,2]
        bgra[:,:,1] = arr[:,:,1]
        bgra[:,:,2] = arr[:,:,0]
        bgra[:,:,3] = 255
        frames.append(bgra)
    return frames

def write_fb(data):
    with open(FB, "wb") as f:
        f.write(data.tobytes())

def blue_flash():
    blue = np.zeros((H, W, 4), dtype=np.uint8)
    blue[:,:,2] = 255   # R=0, G=0, B=255 → azul
    blue[:,:,3] = 255
    write_fb(blue)

def white_flash():
    white = np.full((H, W, 4), 255, dtype=np.uint8)
    write_fb(white)

print("Cargando caras de BMO...", flush=True)

# Pre-cargar todos los frames
all_frames = {}
for folder, label in STATES:
    all_frames[folder] = load_frames(folder)
    print(f"  {label}: {len(all_frames[folder])} frame(s)", flush=True)

print("\n🎬 BMO FACE SHOW - FRAMEBUFFER DIRECTO")
print("Presiona Ctrl+C para salir\n", flush=True)

try:
    ciclo = 0
    while True:
        for folder, label in STATES:
            frames = all_frames[folder]
            n = len(frames)
            print(f"[{label}] ({n} frames) ", end="", flush=True)

            for i in range(n):
                write_fb(frames[i])
                delay = 0.08 if folder == "speaking" else 0.5
                time.sleep(delay)

            # Flash azul entre caras
            blue_flash()
            time.sleep(0.15)
            
            # Si tiene 1 solo frame, mostrar un poco más
            if n == 1:
                time.sleep(1)

            print("✓", flush=True)

        ciclo += 1
        print(f"\n--- Ciclo {ciclo} completo ---\n", flush=True)

except KeyboardInterrupt:
    print("\n\nShow terminado. Volviendo a blanco...", flush=True)
    white_flash()
    time.sleep(0.5)
