#!/usr/bin/env python3
"""
Be More Agent 🤖
A Local, Offline-First AI Agent for Raspberry Pi

Copyright (c) 2026 brenpoly
Licensed under the MIT License
Source: https://github.com/brenpoly/be-more-agent

DISCLAIMER:
This software is provided "as is", without warranty of any kind.
This project is a generic framework and includes no copyrighted assets.
"""
import tkinter as tk
import datetime
import traceback
import logging

import atexit
import ollama

from config import CURRENT_CONFIG, TEXT_MODEL
from states import BotStates
from system_prompt import get_system_prompt
from display import DisplayManager
from audio import AudioManager
from actions import ActionRouter
from chat import ChatPipeline
from memory import load_chat_history, save_chat_history

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("agent")


# ---------------------------------------------------------------------------
# BotGUI — thin orchestrator
# ---------------------------------------------------------------------------

class BotGUI:
    """Wires together display, audio, actions, and chat modules."""

    def __init__(self, master):
        self.master = master
        self.exiting = False

        # --- Display ---
        self.display = DisplayManager(
            master,
            on_exit=self._on_escape,
            on_ptt=self._on_ptt,
            on_interrupt=self._on_interrupt,
        )

        # --- Audio ---
        self.audio = AudioManager(
            state_callback=self.display.set_state,
            pump_callback=self.display.master.update,
        )

        # --- Actions ---
        self.actions = ActionRouter(
            display=self.display,
            audio=self.audio,
        )

        # --- Memory ---
        extras = CURRENT_CONFIG.get("system_prompt_extras", "")
        self.permanent_memory = load_chat_history(extras)
        self.session_memory = []
        self.memory_ref = {
            "permanent": self.permanent_memory,
            "session": self.session_memory,
            "save": self._save_memory,
        }

        # --- Chat ---
        self.chat = ChatPipeline(
            display=self.display,
            audio=self.audio,
            actions=self.actions,
            memory=self.memory_ref,
        )

        atexit.register(self._safe_exit)

        # --- Start ---
        self.display.master.after(100, self._main_loop)

    # ------------------------------------------------------------------
    #  Main loop
    # ------------------------------------------------------------------

    def _main_loop(self):
        try:
            # Warm up
            self.audio.warm_up()
            self.audio.start_tts_worker()

            while not self.exiting:
                trigger = self.audio.detect_wake_word_or_ptt()

                if self.audio.interrupted.is_set():
                    self.audio.interrupted.clear()
                    self.display.set_state(BotStates.IDLE, "Resetting...")
                    continue

                log.info(f"Wake word detected! source={trigger}")
                self.display.set_state(BotStates.ANTENAS, "Hey!")

                # Record
                audio_file = None
                if trigger == "PTT":
                    audio_file = self.audio.record_voice_ptt()
                else:
                    audio_file = self.audio.record_voice_adaptive()

                if not audio_file:
                    log.info("No audio captured, going back to idle")
                    self.display.set_state(BotStates.IDLE, "Heard nothing.")
                    continue

                # Transcribe
                user_text = self.audio.transcribe_audio(audio_file)
                if not user_text:
                    log.info("Transcription empty, going back to idle")
                    self.display.set_state(
                        BotStates.IDLE, "Transcription empty.")
                    continue

                log.info(f'User said: "{user_text}"')
                self.display.append_text(f"YOU: {user_text}")
                self.audio.interrupted.clear()

                # Chat
                self.chat.handle(user_text)

        except Exception as e:
            traceback.print_exc()
            self.display.set_state(
                BotStates.ERROR, f"Fatal Error: {str(e)[:40]}")

    # ------------------------------------------------------------------
    #  Input handlers
    # ------------------------------------------------------------------

    def _on_escape(self, event=None):
        self._safe_exit()

    def _on_ptt(self, event=None):
        self.audio.handle_ptt_toggle(self.display.current_status_text)

    def _on_interrupt(self, event=None):
        if self.display.current_state in (BotStates.SPEAKING,
                                           BotStates.THINKING):
            self.audio.handle_interrupt()
            self.display.set_state(BotStates.IDLE, "Interrupted.")

    # ------------------------------------------------------------------
    #  Shutdown
    # ------------------------------------------------------------------

    def _safe_exit(self):
        if self.exiting:
            return
        self.exiting = True
        log.info("SHUTDOWN SEQUENCE")
        self.audio.stop()
        self._save_memory()
        try:
            ollama.generate(model=TEXT_MODEL, prompt="", keep_alive=0)
        except Exception:
            pass
        try:
            self.master.quit()
        except Exception:
            pass

    def _save_memory(self):
        save_chat_history(self.permanent_memory, self.session_memory)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("SYSTEM STARTING")
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()
