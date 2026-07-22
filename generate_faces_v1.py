#!/usr/bin/env python3
"""Regenerate V1 (original) madrugada faces from vision analysis descriptions.
Background: (189, 255, 203) — the correct BMO green."""
import os
from PIL import Image, ImageDraw

FACES_DIR = "/home/mch/Projects/be-more-agent/faces"
W, H = 800, 480
GREEN = (189, 255, 203)
BLACK = (0, 0, 0)
PINK = (255, 182, 193)
WHITE = (255, 255, 255)
RED = (255, 50, 50)

def auto_save(name, frame_num, draw_fn):
    d = os.path.join(FACES_DIR, name)
    os.makedirs(d, exist_ok=True)
    img = Image.new("RGBA", (W, H), GREEN)
    draw = ImageDraw.Draw(img)
    draw_fn(draw)
    path = os.path.join(d, f"{frame_num:02d}.png")
    img.save(path)
    print(f"  ✓ {name}/{frame_num:02d}.png")

def line(d, xy, w=6):   d.line(xy, fill=BLACK, width=w)
def arc(d, bb, s, e, w=6): d.arc(bb, s, e, fill=BLACK, width=w)
def ell(d, bb, fill=BLACK, outline=None, w=6): d.ellipse(bb, fill=fill, outline=outline, width=w)
def poly(d, pts, fill=BLACK): d.polygon(pts, fill=fill)

# ═══════════════════════════════════════
#  V1 FACES — reconstructed from vision_analyze data
# ═══════════════════════════════════════

def gen_blink_v1():
    """5-frame blink: circles open → half-closed → closed arches → half-closed → circles open"""
    # Frame 1: open circles
    def f1(d):
        ell(d, [230, 150, 340, 260], fill=None, outline=BLACK, w=5)
        ell(d, [460, 150, 570, 260], fill=None, outline=BLACK, w=5)
        ell(d, [270, 195, 300, 225]); ell(d, [500, 195, 530, 225])
        arc(d, [330, 270, 470, 310], 0, 180, w=5)
    auto_save("blink", 1, f1)

    def f2(d):
        line(d, [230, 180, 340, 180]); line(d, [460, 180, 570, 180])
        ell(d, [275, 195, 305, 225]); ell(d, [495, 195, 525, 225])
        arc(d, [330, 270, 470, 310], 0, 180, w=5)
    auto_save("blink", 2, f2)

    def f3(d):
        arc(d, [240, 160, 340, 220], 200, 340, w=5)
        arc(d, [460, 160, 560, 220], 200, 340, w=5)
        line(d, [360, 280, 440, 280])
    auto_save("blink", 3, f3)

    def f4(d):
        line(d, [230, 180, 340, 180]); line(d, [460, 180, 570, 180])
        ell(d, [275, 195, 305, 225]); ell(d, [495, 195, 525, 225])
        arc(d, [330, 270, 470, 310], 0, 180, w=5)
    auto_save("blink", 4, f4)

    def f5(d):
        ell(d, [230, 150, 340, 260], fill=None, outline=BLACK, w=5)
        ell(d, [460, 150, 570, 260], fill=None, outline=BLACK, w=5)
        ell(d, [270, 195, 300, 225]); ell(d, [500, 195, 530, 225])
        arc(d, [330, 270, 470, 310], 0, 180, w=5)
    auto_save("blink", 5, f5)

def gen_corazon_v1():
    """Heart eyes animated: grande → mediano → pequeño → media grande (heartbeat)"""
    HEART = [
        [0,0,1,1,0,0,1,1,0,0],
        [0,1,1,1,1,1,1,1,1,0],
        [1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,0,0,0,0],
    ]
    def draw_heart(d, cx, cy, pix):
        for ri, row in enumerate(HEART):
            for ci, p in enumerate(row):
                if p:
                    x = cx - len(row)//2 * pix + ci * pix
                    y = cy - len(HEART)//2 * pix + ri * pix
                    d.rectangle([x, y, x+pix, y+pix], fill=RED)

    # Frame 1: grande (PIX=10)
    def f1(d):
        draw_heart(d, 275, 195, 10); draw_heart(d, 525, 195, 10)
        arc(d, [340, 285, 460, 330], 0, 180, w=5)
    auto_save("corazon", 1, f1)

    # Frame 2: mediano (PIX=8)
    def f2(d):
        draw_heart(d, 275, 195, 8); draw_heart(d, 525, 195, 8)
        arc(d, [340, 285, 460, 330], 0, 180, w=5)
    auto_save("corazon", 2, f2)

    # Frame 3: pequeño (PIX=6)
    def f3(d):
        draw_heart(d, 275, 195, 6); draw_heart(d, 525, 195, 6)
        arc(d, [340, 285, 460, 330], 0, 180, w=5)
    auto_save("corazon", 3, f3)

    # Frame 4: media grande (PIX=9)
    def f4(d):
        draw_heart(d, 275, 195, 9); draw_heart(d, 525, 195, 9)
        arc(d, [340, 285, 460, 330], 0, 180, w=5)
    auto_save("corazon", 4, f4)

def gen_enojado_v1():
    """Circle eyes + 'pleading' brows + small smile — V1 original (nervous, not angry)"""
    def f1(d):
        ell(d, [230, 150, 340, 260], fill=None, outline=BLACK, w=5)
        ell(d, [460, 150, 570, 260], fill=None, outline=BLACK, w=5)
        ell(d, [270, 195, 300, 225]); ell(d, [500, 195, 530, 225])
        # Pleading brows: left rises L→R, right falls L→R
        line(d, [230, 120, 310, 100])   # left brow \ 
        line(d, [490, 100, 570, 120])   # right brow /
        arc(d, [350, 285, 450, 320], 0, 180, w=5)  # small smile
    auto_save("enojado", 1, f1)

def gen_feliz_v1():
    """Arched closed eyes (∩∩) + blush + smile — V1 original"""
    def f1(d):
        arc(d, [240, 150, 360, 230], 200, 340, w=5)
        arc(d, [440, 150, 560, 230], 200, 340, w=5)
        ell(d, [170, 240, 220, 275], fill=PINK)
        ell(d, [580, 240, 630, 275], fill=PINK)
        arc(d, [330, 270, 470, 320], 0, 180, w=5)
    auto_save("feliz", 1, f1)

def gen_shrek_cat_v1():
    """Large black eyes + catchlight + frown — V1 original"""
    def f1(d):
        ell(d, [210, 120, 370, 280], fill=BLACK)
        ell(d, [430, 120, 590, 280], fill=BLACK)
        ell(d, [225, 135, 245, 155], fill=WHITE)
        ell(d, [445, 135, 465, 155], fill=WHITE)
        arc(d, [350, 290, 450, 330], 180, 360, w=5)  # frown
    auto_save("shrek_cat", 1, f1)

def gen_sorprendido_v1():
    """Circle outline eyes + pupils + raised brows + small O mouth — V1 original"""
    def f1(d):
        ell(d, [230, 150, 340, 260], fill=None, outline=BLACK, w=5)
        ell(d, [460, 150, 570, 260], fill=None, outline=BLACK, w=5)
        ell(d, [270, 195, 300, 225]); ell(d, [500, 195, 530, 225])
        arc(d, [230, 100, 340, 140], 20, 160, w=5)
        arc(d, [460, 100, 570, 140], 20, 160, w=5)
        ell(d, [380, 295, 420, 335], fill=None, outline=BLACK, w=5)  # small O mouth
    auto_save("sorprendido", 1, f1)

def gen_sospechoso_v1():
    """Asymmetrical: left eye open semi-circle, right eye closed line, slanted brows, small mouth"""
    def f1(d):
        arc(d, [240, 150, 350, 260], 180, 360, w=5)  # left eye open semi
        ell(d, [275, 195, 315, 235])                    # left pupil
        line(d, [460, 210, 560, 210])                   # right eye closed line
        line(d, [230, 130, 350, 110])                   # left brow up
        line(d, [570, 110, 450, 130])                   # right brow up
        arc(d, [370, 290, 430, 315], 0, 180, w=4)      # small subtle smile
    auto_save("sospechoso", 1, f1)

# ═══════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("🎨 Regenerando V1 (originales madrugada)...")
    gens = [
        ("blink", gen_blink_v1),
        ("corazon", gen_corazon_v1),
        ("enojado", gen_enojado_v1),
        ("feliz", gen_feliz_v1),
        ("shrek_cat", gen_shrek_cat_v1),
        ("sorprendido", gen_sorprendido_v1),
        ("sospechoso", gen_sospechoso_v1),
    ]
    for name, fn in gens:
        print(f"\n  {name}...")
        fn()
    print(f"\n✅ V1 regeneradas en {FACES_DIR}")
