"""GUI / display subsystem: tkinter window, animations, state rendering."""
import tkinter as tk
from tkinter import ttk
import os
import random
import logging
from PIL import Image, ImageTk

from states import BotStates

logger = logging.getLogger(__name__)

BG_WIDTH, BG_HEIGHT = 800, 480
OVERLAY_WIDTH, OVERLAY_HEIGHT = 400, 300


class DisplayManager:
    """Manages the tkinter GUI: background animations, overlay, HUD text."""

    def __init__(self, master, on_exit, on_ptt, on_interrupt):
        self.master = master
        master.title("Pi Assistant")
        master.geometry("800x480+0+0")
        master.config(cursor='none')
        master.bind('<Escape>', on_exit)
        master.bind('<Return>', on_ptt)
        master.bind('<space>', on_interrupt)

        self.current_state = BotStates.WARMUP
        self.animations = {}
        self.current_frame_index = 0
        self.current_overlay_image = None
        self.idle_emotion_timer = None
        self.idle_emotion_faces = [
            "feliz", "enojado", "sorprendido",
            "sospechoso", "shrek_cat", "blink", "antenas", "corazon",
        ]

        # GUI widgets
        self.background_label = tk.Label(master)
        self.background_label.place(x=0, y=0, width=BG_WIDTH, height=BG_HEIGHT)
        self.background_label.bind('<Button-1>', self._toggle_hud)

        self.overlay_label = tk.Label(master, bg='black')
        self.overlay_label.bind('<Button-1>', self._toggle_hud)

        self.response_text = tk.Text(
            master, height=6, width=60, wrap=tk.WORD,
            state=tk.DISABLED, bg="#ffffff", fg="#000000",
            font=('Arial', 12))

        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = ttk.Label(
            master, textvariable=self.status_var,
            background="#2e2e2e", foreground="white")

        self.exit_button = ttk.Button(
            master, text="Exit & Save", command=on_exit)

        self.load_animations()
        self.update_animation()

    # ------------------------------------------------------------------
    #  Animation loading
    # ------------------------------------------------------------------

    def load_animations(self):
        base_path = "faces"
        if os.path.exists(base_path):
            all_states = sorted([
                d for d in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, d))
            ])
        else:
            all_states = ["idle"]

        for state in all_states:
            folder = os.path.join(base_path, state)
            self.animations[state] = []
            if os.path.exists(folder):
                files = sorted([
                    f for f in os.listdir(folder)
                    if f.lower().endswith('.png')
                ])
                for f in files:
                    img = Image.open(os.path.join(folder, f)).resize(
                        (BG_WIDTH, BG_HEIGHT))
                    self.animations[state].append(ImageTk.PhotoImage(img))
            if not self.animations[state]:
                if state in self.animations.get("idle", []):
                    self.animations[state] = self.animations["idle"]
                else:
                    blank = Image.new(
                        'RGB', (BG_WIDTH, BG_HEIGHT), color='#0000FF')
                    self.animations[state].append(ImageTk.PhotoImage(blank))

    # ------------------------------------------------------------------
    #  Animation loop
    # ------------------------------------------------------------------

    def update_animation(self):
        frames = (self.animations.get(self.current_state, [])
                  or self.animations.get(BotStates.IDLE, []))
        if not frames:
            self.master.after(500, self.update_animation)
            return

        if self.current_state == BotStates.SPEAKING:
            if len(frames) > 1:
                self.current_frame_index = random.randint(1, len(frames) - 1)
            else:
                self.current_frame_index = 0
        else:
            self.current_frame_index = (self.current_frame_index + 1) % len(frames)

        self.background_label.config(image=frames[self.current_frame_index])

        speed = 50 if self.current_state == BotStates.SPEAKING else 500
        self.master.after(speed, self.update_animation)

    # ------------------------------------------------------------------
    #  State transitions
    # ------------------------------------------------------------------

    def set_state(self, state, msg="", cam_path=None):
        # Cancel idle emotion timer
        if self.idle_emotion_timer:
            try:
                self.master.after_cancel(self.idle_emotion_timer)
            except Exception:
                pass
            self.idle_emotion_timer = None

        # Update state synchronously so animation loop picks it up immediately
        if msg:
            logger.info(f"STATE → {state.upper()}: {msg}")
        if self.current_state != state:
            self.current_state = state
            self.current_frame_index = 0
            # Show first frame immediately (animation loop is blocked in _listen_loop)
            frames = self.animations.get(self.current_state)
            if frames:
                self.background_label.config(image=frames[0])
                self.master.update()
                logger.info(f"DISPLAY: showing {self.current_state} frame 0/{len(frames)}")
            else:
                logger.warning(f"DISPLAY: no frames for {self.current_state}, anim keys={list(self.animations.keys())[:5]}...")
        if msg:
            self.status_var.set(msg)

        # IDLE → DORMIDO (sleeping face)
        if state == BotStates.IDLE:
            self.current_state = BotStates.DORMIDO
            self.current_frame_index = 0
            frames = self.animations.get(BotStates.DORMIDO)
            if frames:
                self.background_label.config(image=frames[0])
                self.master.update()
            self.master.after(50, self.update_animation)
            logger.info(f"DISPLAY: DORMIDO override, frame 0/{len(frames) if frames else 'none'}")

        # Defer overlay/camera image handling
        def _update_overlay():
            if (cam_path and os.path.exists(cam_path)
                    and state in [BotStates.THINKING, BotStates.SPEAKING,
                                  BotStates.CAMERA]):
                try:
                    img = Image.open(cam_path).resize(
                        (OVERLAY_WIDTH, OVERLAY_HEIGHT))
                    self.current_overlay_image = ImageTk.PhotoImage(img)
                    self.overlay_label.config(
                        image=self.current_overlay_image)
                    self.overlay_label.place(x=200, y=90)
                except Exception:
                    pass
            else:
                self.overlay_label.place_forget()

        self.master.after(0, _update_overlay)

    def schedule_idle_emotion(self):
        """After 20s of idle, show a random emotion for 4s."""
        if self.current_state != BotStates.IDLE:
            return
        candidates = [f for f in self.idle_emotion_faces
                      if f in self.animations]
        if not candidates:
            return
        self.idle_emotion_timer = self.master.after(
            20000, lambda: self._do_idle_emotion(candidates))

    def _do_idle_emotion(self, candidates):
        if self.current_state != BotStates.IDLE:
            return
        face = random.choice(candidates)
        self.current_state = face
        self.current_frame_index = 0
        logger.info(f"IDLE EMOTION → {face}")

        def back_to_idle():
            if self.current_state == face:
                self.set_state(BotStates.IDLE, f"Idle (was {face})")
        self.idle_emotion_timer = self.master.after(4000, back_to_idle)

    # ------------------------------------------------------------------
    #  Text output
    # ------------------------------------------------------------------

    def append_text(self, text, newline=True):
        def _update():
            self.response_text.config(state=tk.NORMAL)
            if newline:
                self.response_text.insert(tk.END, text + "\n")
            else:
                self.response_text.insert(tk.END, text)
            self.response_text.see(tk.END)
            self.response_text.config(state=tk.DISABLED)
        self.master.after(0, _update)

    def stream_text(self, chunk):
        def _update():
            self.response_text.config(state=tk.NORMAL)
            self.response_text.insert(tk.END, chunk)
            self.response_text.see(tk.END)
            self.response_text.config(state=tk.DISABLED)
        self.master.after(0, _update)

    # ------------------------------------------------------------------
    #  HUD toggle
    # ------------------------------------------------------------------

    def _toggle_hud(self, event=None):
        try:
            if self.response_text.winfo_ismapped():
                self.response_text.place_forget()
                self.status_label.place_forget()
                self.exit_button.place_forget()
            else:
                self.response_text.place(relx=0.5, rely=0.82, anchor=tk.S)
                self.status_label.place(
                    relx=0.5, rely=1.0, anchor=tk.S, relwidth=1)
                self.exit_button.place(x=10, y=10)
        except tk.TclError:
            pass

    @property
    def current_status_text(self):
        return self.status_var.get()
