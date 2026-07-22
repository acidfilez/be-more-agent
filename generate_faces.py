#!/usr/bin/env python3
"""Generates new BMO face expressions in the same minimalist style.
800x480, mint green background, thick black lines with rounded caps."""

import os, math
from PIL import Image, ImageDraw

FACES_DIR = "/home/mch/Projects/be-more-agent/faces"
W, H = 800, 480
BMO_GREEN = (189, 255, 203)  # verde original de las caras existentes
BLACK = (0, 0, 0)
PINK = (255, 182, 193)       # blush suave
RED = (255, 50, 50)

def make_dir(name):
    path = os.path.join(FACES_DIR, name)
    os.makedirs(path, exist_ok=True)
    return path

def draw_bg(draw):
    draw.rectangle([0, 0, W, H], fill=BMO_GREEN)

def save_face(name, filename, draw_fn):
    img = Image.new("RGBA", (W, H), BMO_GREEN)
    draw = ImageDraw.Draw(img)
    draw_fn(draw)
    path = os.path.join(FACES_DIR, name, filename)
    img.save(path)
    print(f"  ✓ {name}/{filename}")
    return path

def auto_save(name, frame_num, draw_fn):
    """Save with standard naming: NN.png"""
    return save_face(name, f"{frame_num:02d}.png", draw_fn)

# ─── LÍNEA NEGRA GRUESA (helper) ───
def thick_line(draw, xy, width=6):
    draw.line(xy, fill=BLACK, width=width)

def thick_arc(draw, bbox, start, end, width=6):
    draw.arc(bbox, start, end, fill=BLACK, width=width)

def thick_ellipse(draw, bbox, fill=BLACK, outline=None, width=6):
    draw.ellipse(bbox, fill=fill, outline=outline, width=width)

# ═══════════════════════════════════════
#  1. TRISTE (sad) — lágrima, boca triste
# ═══════════════════════════════════════
def gen_triste():
    d = make_dir("triste")

    # Frame 1: ojos grandes tristes, boca hacia abajo
    def f1(draw):
        # Ojos grandes (círculos abiertos)
        thick_ellipse(draw, [250, 140, 370, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [430, 140, 550, 260], fill=None, outline=BLACK)
        # Pupilas
        thick_ellipse(draw, [285, 185, 335, 235], fill=BLACK)
        thick_ellipse(draw, [465, 185, 515, 235], fill=BLACK)
        # Cejas tristes (\/)
        thick_line(draw, [230, 100, 310, 130])
        thick_line(draw, [570, 130, 490, 100])
        # Boca triste
        thick_arc(draw, [320, 300, 480, 360], 200, 340)
        # Lágrima
        thick_ellipse(draw, [370, 270, 390, 310], fill=(180, 210, 255))
    auto_save("triste", 1, f1)

    # Frame 2: lágrima más grande
    def f2(draw):
        thick_ellipse(draw, [250, 140, 370, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [430, 140, 550, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [285, 185, 335, 235], fill=BLACK)
        thick_ellipse(draw, [465, 185, 515, 235], fill=BLACK)
        thick_line(draw, [230, 100, 310, 130])
        thick_line(draw, [570, 130, 490, 100])
        thick_arc(draw, [320, 300, 480, 360], 200, 340)
        # Lágrima grande rodando
        thick_ellipse(draw, [365, 270, 395, 330], fill=(180, 210, 255))
    auto_save("triste", 2, f2)

# ═══════════════════════════════════════
#  2. GUIÑO (wink) — un ojo cerrado
# ═══════════════════════════════════════
def gen_guino():
    d = make_dir("guino")

    def f1(draw):
        # Ojo izquierdo abierto
        thick_ellipse(draw, [240, 150, 360, 270], fill=None, outline=BLACK)
        thick_ellipse(draw, [275, 195, 325, 245], fill=BLACK)
        # Ojo derecho cerrado (guiño)
        thick_line(draw, [430, 210, 560, 210])
        # Sonrisa coqueta
        thick_arc(draw, [330, 310, 470, 360], 0, 180)
        # Mejilla sonrosada
        thick_ellipse(draw, [500, 280, 550, 310], fill=PINK)
    auto_save("guino", 1, f1)

# ═══════════════════════════════════════
#  3. FIESTA (party) — gorrito, sonrisa grande
# ═══════════════════════════════════════
def gen_fiesta():
    d = make_dir("fiesta")

    def f1(draw):
        # Gorrito de fiesta
        thick_line(draw, [310, 80, 490, 80])
        draw.polygon([(400, 15), (340, 85), (460, 85)], fill=(255, 200, 50), outline=BLACK)
        # Pompón
        thick_ellipse(draw, [388, 5, 412, 25], fill=RED)
        # Ojos felices (arqueados)
        thick_arc(draw, [230, 150, 350, 220], 200, 340)
        thick_arc(draw, [450, 150, 570, 220], 200, 340)
        # Sonrisa grande
        thick_arc(draw, [300, 280, 500, 380], 0, 180)
        # Confeti
        colors = [(255,50,50),(255,200,50),(50,200,255),(255,100,200)]
        for x,y in [(150,100),(650,80),(200,200),(600,150),(130,350),(670,300)]:
            thick_ellipse(draw, [x-5,y-5,x+5,y+5], fill=colors[(x+y)%4])
    auto_save("fiesta", 1, f1)

# ═══════════════════════════════════════
#  4. BESO (kiss) — boca de pato, corazoncito
# ═══════════════════════════════════════
def gen_beso():
    d = make_dir("beso")

    def f1(draw):
        # Ojos cerrados enamorados
        thick_arc(draw, [240, 160, 350, 230], 200, 340)
        thick_arc(draw, [450, 160, 560, 230], 200, 340)
        # Boca beso (labios fruncidos)
        thick_ellipse(draw, [370, 290, 430, 330], fill=RED, outline=BLACK)
        # Corazoncito flotante
        center_x, center_y = 580, 280
        size = 20
        draw.polygon([
            (center_x, center_y - size//2),
            (center_x - size, center_y + size//4),
            (center_x - size//2, center_y + size),
            (center_x, center_y + size//2),
            (center_x + size//2, center_y + size),
            (center_x + size, center_y + size//4),
        ], fill=RED)
    auto_save("beso", 1, f1)

# ═══════════════════════════════════════
#  5. DORMIDO (sleeping) — zzz
# ═══════════════════════════════════════
def gen_dormido():
    d = make_dir("dormido")

    # Frame 1: ojos cerrados
    def f1(draw):
        thick_line(draw, [260, 210, 340, 210])
        thick_line(draw, [460, 210, 540, 210])
        # Boca pequeña
        thick_arc(draw, [370, 280, 430, 310], 0, 180)
        # Z's
        draw.text((560, 140), "z", fill=(100, 100, 100), font=None)
        draw.text((580, 110), "z", fill=(80, 80, 80), font=None)
        draw.text((600, 80),  "z", fill=(60, 60, 60), font=None)
    auto_save("dormido", 1, f1)

    # Frame 2: ojos más relajados
    def f2(draw):
        thick_line(draw, [260, 215, 340, 215])
        thick_line(draw, [460, 215, 540, 215])
        thick_arc(draw, [370, 285, 430, 310], 0, 180)
        draw.text((550, 150), "z", fill=(100, 100, 100), font=None)
        draw.text((570, 120), "Z", fill=(80, 80, 80), font=None)
        draw.text((590, 90),  "Z", fill=(60, 60, 60), font=None)
    auto_save("dormido", 2, f2)

# ═══════════════════════════════════════
#  6. CONFUNDIDO (confused) — ??
# ═══════════════════════════════════════
def gen_confundido():
    d = make_dir("confundido")

    def f1(draw):
        # Ojos: uno normal, uno entrecerrado
        thick_ellipse(draw, [240, 150, 360, 270], fill=None, outline=BLACK)
        thick_ellipse(draw, [275, 195, 325, 245], fill=BLACK)
        # Ojo derecho entrecerrado
        thick_line(draw, [440, 200, 560, 220])
        # Cejas: una levantada, una normal
        thick_line(draw, [230, 100, 370, 120])  # levantada
        thick_line(draw, [580, 130, 450, 100])  # fruncida
        # Boca torcida
        thick_line(draw, [360, 320, 440, 300])
        # Signo de interrogación
        draw.text((580, 100), "?", fill=(100, 100, 100), font=None)
    auto_save("confundido", 1, f1)

# ═══════════════════════════════════════
#  7. ASUSTADO (scared) — ojos enormes
# ═══════════════════════════════════════
def gen_asustado():
    d = make_dir("asustado")

    def f1(draw):
        # Ojos enormes
        thick_ellipse(draw, [210, 110, 370, 270], fill=None, outline=BLACK)
        thick_ellipse(draw, [430, 110, 590, 270], fill=None, outline=BLACK)
        # Pupilas pequeñas (contraídas)
        thick_ellipse(draw, [265, 175, 315, 225], fill=BLACK)
        thick_ellipse(draw, [485, 175, 535, 225], fill=BLACK)
        # Cejas levantadas
        thick_arc(draw, [210, 70, 370, 120], 20, 160)
        thick_arc(draw, [430, 70, 590, 120], 20, 160)
        # Boca abierta (grito)
        thick_ellipse(draw, [340, 300, 460, 400], fill=None, outline=BLACK)
        thick_ellipse(draw, [370, 330, 430, 380], fill=BLACK)
        # Sudor
        thick_line(draw, [300, 80, 290, 60])
        thick_line(draw, [290, 60, 305, 55])
        thick_line(draw, [510, 90, 500, 70])
        thick_line(draw, [500, 70, 515, 65])
    auto_save("asustado", 1, f1)

# ═══════════════════════════════════════
#  8. LLORANDO (crying) — lágrimas
# ═══════════════════════════════════════
def gen_llorando():
    d = make_dir("llorando")

    # Frame 1: lágrimas pequeñas
    def f1(draw):
        thick_ellipse(draw, [240, 140, 360, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [440, 140, 560, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [275, 185, 325, 235], fill=BLACK)
        thick_ellipse(draw, [475, 185, 525, 235], fill=BLACK)
        thick_line(draw, [230, 100, 310, 130])
        thick_line(draw, [570, 130, 490, 100])
        # Boca abierta
        thick_ellipse(draw, [360, 300, 440, 350], fill=None, outline=BLACK)
        thick_ellipse(draw, [370, 310, 430, 345], fill=BLACK)
        # Lágrimas
        thick_ellipse(draw, [365, 265, 385, 300], fill=(180, 210, 255))
        thick_ellipse(draw, [415, 265, 435, 300], fill=(180, 210, 255))
    auto_save("llorando", 1, f1)

    # Frame 2: lágrimas grandes
    def f2(draw):
        thick_ellipse(draw, [240, 140, 360, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [440, 140, 560, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [275, 185, 325, 235], fill=BLACK)
        thick_ellipse(draw, [475, 185, 525, 235], fill=BLACK)
        thick_line(draw, [230, 100, 310, 130])
        thick_line(draw, [570, 130, 490, 100])
        thick_ellipse(draw, [360, 300, 440, 350], fill=None, outline=BLACK)
        thick_ellipse(draw, [370, 310, 430, 345], fill=BLACK)
        # Lágrimas grandes
        thick_ellipse(draw, [360, 265, 390, 320], fill=(180, 210, 255))
        thick_ellipse(draw, [410, 265, 440, 320], fill=(180, 210, 255))
        thick_ellipse(draw, [340, 310, 365, 340], fill=(180, 210, 255))
        thick_ellipse(draw, [435, 310, 460, 340], fill=(180, 210, 255))
    auto_save("llorando", 2, f2)

# ═══════════════════════════════════════
#  9. SONRISA (gentle smile)
# ═══════════════════════════════════════
def gen_sonrisa():
    d = make_dir("sonrisa")

    def f1(draw):
        # Ojos arqueados (contentos)
        thick_arc(draw, [240, 150, 360, 230], 200, 340)
        thick_arc(draw, [440, 150, 560, 230], 200, 340)
        # Sonrisa suave
        thick_arc(draw, [330, 290, 470, 340], 0, 180)
        # Mejillas
        thick_ellipse(draw, [190, 250, 230, 280], fill=PINK)
        thick_ellipse(draw, [570, 250, 610, 280], fill=PINK)
    auto_save("sonrisa", 1, f1)

# ═══════════════════════════════════════
#  10. FRIO (cold) — azul, tiritando
# ═══════════════════════════════════════
def gen_frio():
    d = make_dir("frio")

    def f1(draw):
        # Fondo azul pálido
        draw.rectangle([0, 0, W, H], fill=(200, 220, 240))
        # Ojos: uno abierto, el otro semicerrado
        thick_ellipse(draw, [260, 160, 350, 250], fill=None, outline=BLACK)
        thick_ellipse(draw, [285, 190, 325, 230], fill=BLACK)
        thick_line(draw, [440, 210, 540, 210])
        # Boca temblorosa (zigzag suave)
        thick_line(draw, [360, 310, 380, 305, 400, 310, 420, 305, 440, 310])
        # Líneas de frío
        for i in range(3):
            x = 150 + i*30
            y = 100 + i*20
            thick_line(draw, [x, y, x+15, y-15])
        for i in range(3):
            x = 620 + i*30
            y = 350 - i*20
            thick_line(draw, [x, y, x+15, y-15])
    auto_save("frio", 1, f1)

# ═══════════════════════════════════════
#  11. TIMIDO (shy) — sonrojo, mirada lateral
# ═══════════════════════════════════════
def gen_timido():
    d = make_dir("timido")

    def f1(draw):
        # Ojos: mirando hacia abajo y al lado
        thick_arc(draw, [250, 160, 350, 230], 20, 160)
        thick_arc(draw, [450, 160, 550, 230], 20, 160)
        # Pupilas descentradas
        thick_ellipse(draw, [260, 195, 300, 225], fill=BLACK)
        thick_ellipse(draw, [500, 195, 540, 225], fill=BLACK)
        # Sonrisa tímida
        thick_arc(draw, [350, 300, 450, 330], 0, 180)
        # Mucho sonrojo
        thick_ellipse(draw, [180, 240, 240, 290], fill=PINK)
        thick_ellipse(draw, [560, 240, 620, 290], fill=PINK)
        # Líneas diagonales (nervios)
        thick_line(draw, [170, 130, 185, 145])
        thick_line(draw, [185, 120, 200, 135])
        thick_line(draw, [600, 120, 615, 135])
        thick_line(draw, [615, 130, 630, 145])
    auto_save("timido", 1, f1)

# ═══════════════════════════════════════
#  12. HAMBRE (hungry) — lengua afuera
# ═══════════════════════════════════════
def gen_hambre():
    d = make_dir("hambre")

    def f1(draw):
        # Ojos redondos (normales)
        thick_ellipse(draw, [240, 140, 360, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [440, 140, 560, 260], fill=None, outline=BLACK)
        thick_ellipse(draw, [275, 185, 325, 235], fill=BLACK)
        thick_ellipse(draw, [475, 185, 525, 235], fill=BLACK)
        # Boca abierta con lengua
        thick_ellipse(draw, [340, 290, 460, 370], fill=None, outline=BLACK)
        thick_ellipse(draw, [360, 310, 440, 350], fill=(255, 100, 100))  # lengua
        # Babeo
        thick_ellipse(draw, [450, 360, 465, 400], fill=(180, 210, 255))
    auto_save("hambre", 1, f1)

# ═══════════════════════════════════════
#  13. RISUEÑO (laughing) — carcajada
# ═══════════════════════════════════════
def gen_risueno():
    d = make_dir("risueno")

    # Frame 1: risa moderada
    def f1(draw):
        thick_arc(draw, [220, 160, 340, 240], 200, 340)
        thick_arc(draw, [460, 160, 580, 240], 200, 340)
        thick_ellipse(draw, [340, 280, 460, 380], fill=None, outline=BLACK)
        # Lengua
        thick_ellipse(draw, [365, 310, 435, 360], fill=(255, 100, 100))
        thick_arc(draw, [130, 230, 200, 270], 180, 360)  # mejilla izq
        thick_arc(draw, [600, 230, 670, 270], 180, 360)  # mejilla der
    auto_save("risueno", 1, f1)

    # Frame 2: risa fuerte
    def f2(draw):
        thick_arc(draw, [240, 150, 360, 230], 200, 340)
        thick_arc(draw, [440, 150, 560, 230], 200, 340)
        thick_arc(draw, [340, 270, 460, 380], 350, 190)
        thick_ellipse(draw, [365, 300, 435, 350], fill=(255, 100, 100))
        thick_arc(draw, [120, 220, 200, 270], 180, 360)
        thick_arc(draw, [600, 220, 680, 270], 180, 360)
    auto_save("risueno", 2, f2)

# ═══════════════════════════════════════
#  14. BOSTEZO (yawning) — boca grande
# ═══════════════════════════════════════
def gen_bostezo():
    d = make_dir("bostezo")

    # Frame 1: boca abriéndose
    def f1(draw):
        # Ojos entrecerrados
        thick_line(draw, [250, 210, 350, 210])
        thick_line(draw, [450, 210, 550, 210])
        # Boca grande
        thick_ellipse(draw, [310, 280, 490, 410], fill=None, outline=BLACK)
        thick_ellipse(draw, [330, 290, 470, 350], fill=BLACK)
    auto_save("bostezo", 1, f1)

    # Frame 2: boca cerrada después
    def f2(draw):
        thick_line(draw, [260, 210, 340, 210])
        thick_line(draw, [460, 210, 540, 210])
        thick_line(draw, [360, 320, 440, 320])
    auto_save("bostezo", 2, f2)

# ═══════════════════════════════════════
#  MAIN — generar todas
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("🎨 Generando nuevas caras BMO...")
    generators = [
        ("triste", gen_triste),
        ("guino", gen_guino),
        ("fiesta", gen_fiesta),
        ("beso", gen_beso),
        ("dormido", gen_dormido),
        ("confundido", gen_confundido),
        ("asustado", gen_asustado),
        ("llorando", gen_llorando),
        ("sonrisa", gen_sonrisa),
        ("frio", gen_frio),
        ("timido", gen_timido),
        ("hambre", gen_hambre),
        ("risueno", gen_risueno),
        ("bostezo", gen_bostezo),
    ]
    for name, gen_fn in generators:
        print(f"\n  {name}...")
        gen_fn()
    print(f"\n✅ ¡{len(generators)} nuevas expresiones generadas!")
    print(f"   Ruta: {FACES_DIR}")
