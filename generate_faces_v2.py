#!/usr/bin/env python3
"""Generate V2 of madrugada faces with standard BMO mouth/eye styles."""
import os
from PIL import Image, ImageDraw

FACES_DIR = "/home/mch/Projects/be-more-agent/faces_v2"
W, H = 800, 480
GREEN = (189, 255, 203)
BLACK = (0, 0, 0)
PINK = (255, 182, 193)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
DARK_GREEN = (50, 120, 100)
MED_GREEN = (90, 180, 150)

def auto_save(name, frame_num, draw_fn):
    d = os.path.join(FACES_DIR, name)
    os.makedirs(d, exist_ok=True)
    img = Image.new("RGBA", (W, H), GREEN)
    draw = ImageDraw.Draw(img)
    draw_fn(draw)
    path = os.path.join(d, f"{frame_num:02d}.png")
    img.save(path)
    print(f"  ✓ {name}/{frame_num:02d}.png")

# ─── STANDARD BMO DRAWING HELPERS ───
def line(d, xy, w=6):   d.line(xy, fill=BLACK, width=w)
def arc(d, bb, s, e, w=6): d.arc(bb, s, e, fill=BLACK, width=w)
def ell(d, bb, fill=BLACK, outline=None, w=6): d.ellipse(bb, fill=fill, outline=outline, width=w)

# ─── STANDARD MOUTHS (BMO primaries style) ───

def mouth_neutral(d):      # idle style — straight line
    line(d, [360, 280, 440, 280])

def mouth_smile(d):         # listening style — upward arc ∪
    arc(d, [330, 270, 470, 310], 0, 180, w=5)

def mouth_frown(d):         # inverted smile ∩
    arc(d, [330, 275, 470, 315], 180, 360, w=5)

def mouth_open_teeth(d):    # speaking f2 style — oval + teeth + tongue
    ell(d, [340, 285, 460, 350], fill=MED_GREEN, outline=BLACK, w=5)
    # Teeth bar
    d.rectangle([355, 290, 445, 305], fill=WHITE, outline=BLACK, width=3)
    # Tongue
    arc(d, [370, 320, 430, 345], 0, 180, w=4)

def mouth_open_wide(d):     # speaking f3 style — big open + teeth + tongue
    arc(d, [330, 275, 470, 370], 350, 190, w=5)
    d.rectangle([345, 280, 455, 295], fill=WHITE, outline=BLACK, width=3)
    arc(d, [370, 320, 430, 355], 0, 180, w=4)

def mouth_small_o(d):       # sorprendido style
    ell(d, [380, 295, 420, 335], fill=None, outline=BLACK, w=5)

# ─── STANDARD EYES ───

def eyes_dots(d):           # speaking style — simple dots
    ell(d, [260, 185, 290, 215])
    ell(d, [510, 185, 540, 215])

def eyes_circles(d, pupil=True):    # capturing style — outline + pupil
    ell(d, [230, 150, 340, 260], fill=None, outline=BLACK, w=5)
    ell(d, [460, 150, 570, 260], fill=None, outline=BLACK, w=5)
    if pupil:
        ell(d, [270, 195, 300, 225])
        ell(d, [500, 195, 530, 225])

def eyes_arches(d):         # idle / happy style — ∩∩
    arc(d, [240, 160, 340, 220], 200, 340, w=5)
    arc(d, [460, 160, 560, 220], 200, 340, w=5)

def eyes_line_pupil(d, offset=0):   # thinking style — line + dot
    line(d, [230, 180, 340, 180])
    line(d, [460, 180, 570, 180])
    ell(d, [275 + offset, 195, 305 + offset, 225])
    ell(d, [495 - offset, 195, 525 - offset, 225])

def eyes_large_catchlight(d):   # shrek_cat style — big with white dot
    ell(d, [210, 120, 370, 280], fill=BLACK)
    ell(d, [430, 120, 590, 280], fill=BLACK)
    ell(d, [225, 135, 245, 155], fill=WHITE)  # catchlights
    ell(d, [445, 135, 465, 155], fill=WHITE)

# ─── STANDARD BROWS ───
def brows_angry(d):
    line(d, [220, 120, 320, 150])
    line(d, [580, 150, 480, 120])

def brows_raised(d):
    arc(d, [220, 100, 340, 140], 20, 160, w=4)
    arc(d, [460, 100, 580, 140], 20, 160, w=4)

def brows_side_eye(d):
    line(d, [220, 130, 340, 110])   # left brow up
    line(d, [580, 130, 460, 110])   # right brow up (inverted for side-eye)

def brows_skeptical(d):
    line(d, [230, 120, 340, 135])   # left down
    line(d, [460, 120, 570, 105])   # right up

# ─── CHEEKS ───
def cheeks(d):
    ell(d, [170, 240, 210, 270], fill=PINK)
    ell(d, [590, 240, 630, 270], fill=PINK)

# ═══════════════════════════════════════
#  V2 FACES
# ═══════════════════════════════════════

def gen_blink_v2():
    # 5 frames: open → half → closed → half → open
    # Frame 1: eyes open (circles), smile
    def f1(d):
        eyes_circles(d)
        mouth_smile(d)
    auto_save("blink", 1, f1)

    # Frame 2: half-closed (line+pupil), smile
    def f2(d):
        eyes_line_pupil(d)
        mouth_smile(d)
    auto_save("blink", 2, f2)

    # Frame 3: closed (arches ∩∩), neutral
    def f3(d):
        eyes_arches(d)
        mouth_neutral(d)
    auto_save("blink", 3, f3)

    # Frame 4: half-closed again
    def f4(d):
        eyes_line_pupil(d)
        mouth_smile(d)
    auto_save("blink", 4, f4)

    # Frame 5: open again
    def f5(d):
        eyes_circles(d)
        mouth_smile(d)
    auto_save("blink", 5, f5)

def gen_corazon_v2():
    # Heart eyes (keep!), standard smile, blush
    def f1(d):
        # Pixel hearts as eyes (left and right)
        def heart(cx, cy, s=15):
            pts = [
                (cx, cy - s//2),
                (cx - s, cy + s//4),
                (cx - s//2, cy + s),
                (cx, cy + s//2),
                (cx + s//2, cy + s),
                (cx + s, cy + s//4),
            ]
            d.polygon(pts, fill=RED)
        heart(280, 200)
        heart(520, 200)
        mouth_smile(d)
        cheeks(d)
    auto_save("corazon", 1, f1)

def gen_enojado_v2():
    # Angry: circle eyes, angry brows, FROWN (not smile)
    def f1(d):
        eyes_circles(d)
        brows_angry(d)
        mouth_frown(d)
    auto_save("enojado", 1, f1)

def gen_feliz_v2():
    # Happy: arched eyes, big smile, blush
    def f1(d):
        eyes_arches(d)
        cheeks(d)
        mouth_smile(d)
    auto_save("feliz", 1, f1)

def gen_shrek_cat_v2():
    # Shrek cat: big eyes with catchlight, sad frown
    def f1(d):
        eyes_large_catchlight(d)
        mouth_frown(d)
    auto_save("shrek_cat", 1, f1)

def gen_sorprendido_v2():
    # Surprised: wide eyes, raised brows, OPEN mouth (speaking style)
    def f1(d):
        eyes_circles(d, pupil=True)
        brows_raised(d)
        mouth_open_teeth(d)
    auto_save("sorprendido", 1, f1)

def gen_sospechoso_v2():
    # Suspicious: asymmetrical eyes, skeptical brows, slight smirk
    def f1(d):
        # Left eye: open semi-circle
        arc(d, [240, 150, 350, 260], 180, 360, w=5)
        ell(d, [275, 195, 315, 235])  # pupil
        # Right eye: squint line
        line(d, [460, 210, 560, 210])
        # Skeptical brows
        brows_skeptical(d)
        # Smirk — slight smile on one side
        arc(d, [360, 285, 440, 310], 10, 170, w=5)
    auto_save("sospechoso", 1, f1)

# ═══════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("🎨 Generando V2 de caras de la madrugada...")
    gens = [
        ("blink", gen_blink_v2),
        ("corazon", gen_corazon_v2),
        ("enojado", gen_enojado_v2),
        ("feliz", gen_feliz_v2),
        ("shrek_cat", gen_shrek_cat_v2),
        ("sorprendido", gen_sorprendido_v2),
        ("sospechoso", gen_sospechoso_v2),
    ]
    for name, fn in gens:
        print(f"\n  {name}...")
        fn()
    print(f"\n✅ V2 generadas en {FACES_DIR}")
