"""Chat pipeline: LLM streaming, tool dispatch, response handling."""
import threading
import re
import random
import time
import logging

import ollama

from config import TEXT_MODEL, VISION_MODEL, OLLAMA_OPTIONS, CURRENT_CONFIG
from states import BotStates
from camera import capture_image
from system_prompt import get_system_prompt

logger = logging.getLogger(__name__)

WHO_PATTERNS = [
    r"(?:who(?:'s| is| was)|whos)\s+(.+?)",
    r"(?:quien es|quien)\s+(.+?)",
    r"do\s+you\s+know\s+who\s+(.+?)\s+is",
    r"tell\s+me\s+about\s+(.+?)",
    r"sabes\s+quien\s+es\s+(.+?)",
    r"conoces\s+a\s+(.+?)",
]


class ChatPipeline:
    """Orchestrates the LLM chat flow: thinking, streaming, tool execution,
    TTS queuing, and response finalisation."""

    def __init__(self, display, audio, actions, memory):
        self.display = display
        self.audio = audio
        self.actions = actions
        self.memory = memory

    def handle(self, user_text, img_path=None):
        """Main entry point for a user utterance."""
        # --- Pre-filter: "who is X" ---
        if self._prefilter_who(user_text, img_path):
            return

        # --- Memory reset ---
        if "forget everything" in user_text.lower() or "reset memory" in user_text.lower():
            self.memory["session"] = []
            self.memory["permanent"] = [
                {"role": "system", "content": get_system_prompt(
                    CURRENT_CONFIG.get("system_prompt_extras", ""))}]
            self.memory["save"]()
            self.audio.enqueue_tts("Okay. Memory wiped.")
            self.display.set_state(BotStates.IDLE, "Memory Wiped")
            return

        model = VISION_MODEL if img_path else TEXT_MODEL
        self.display.set_state(BotStates.THINKING, "Thinking...",
                               cam_path=img_path)

        # Build messages
        if img_path:
            messages = [{"role": "user", "content": user_text,
                         "images": [img_path]}]
        else:
            user_msg = {"role": "user", "content": user_text}
            messages = (self.memory["permanent"]
                        + self.memory["session"] + [user_msg])

        self.audio.start_thinking_sound()

        full_response = ""
        sentence_buffer = ""
        is_action_mode = False

        try:
            stream = ollama.chat(
                model=model, messages=messages, stream=True,
                options=OLLAMA_OPTIONS)

            for chunk in stream:
                if self.audio.interrupted.is_set():
                    break

                content = chunk['message']['content']
                full_response += content

                # Detect JSON action mode
                if '{"' in content or "action:" in content.lower():
                    is_action_mode = True
                    self.audio.stop_thinking_sound()
                    continue

                if is_action_mode:
                    continue

                # Switch to speaking mode on first real text
                self.audio.stop_thinking_sound()
                if self.display.current_state != BotStates.SPEAKING:
                    self.display.set_state(
                        BotStates.SPEAKING, "Speaking...", cam_path=img_path)
                    self.display.append_text("BOT: ", newline=False)

                self.display.stream_text(content)
                sentence_buffer += content

                if any(punct in content for punct in ".!?\n"):
                    clean = sentence_buffer.strip()
                    if clean and re.search(r'[a-zA-Z0-9]', clean):
                        self.audio.enqueue_tts(clean)
                    sentence_buffer = ""

            # --- Action mode: execute tool ---
            if is_action_mode:
                result = self._dispatch_action(
                    full_response, user_text, img_path)
                if result is not None:
                    return

            # --- Normal chat: finalize ---
            self.display.append_text("")
            self.memory["session"].append(
                {"role": "assistant", "content": full_response})

            self.audio.wait_for_tts()
            self._end_response(full_response)

        except Exception as e:
            logger.error(f"LLM error: {e}")
            self.display.set_state(BotStates.ERROR, "Brain Freeze!")

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _prefilter_who(self, text, img_path):
        """Bypass LLM for 'who is X' queries."""
        text_clean = text.strip().lower()
        name = None
        for pat in WHO_PATTERNS:
            m = re.match(r"^" + pat + r"\??$", text_clean)
            if m:
                name = m.group(1).strip()
                break
        if not name:
            return False

        logger.info(f"WHO-IS pre-filter: '{name}'")
        result = self.actions.execute(
            {"action": "who_person", "value": name})
        if result and result.startswith("WHO_PERSON::"):
            response = result.split("::", 1)[1]
        else:
            response = f"I don't know who {name} is."

        self.audio.stop_thinking_sound()
        self.display.set_state(
            BotStates.SPEAKING, "Speaking...", cam_path=img_path)
        self.display.append_text("BOT: ", newline=False)
        self.display.append_text(response, newline=True)
        self.audio.enqueue_tts(response)
        self.memory["session"].append(
            {"role": "assistant", "content": response})
        self.audio.wait_for_tts()
        self._end_response(response)
        return True

    def _dispatch_action(self, full_response, user_text, img_path):
        """Parse JSON action from LLM output and execute."""
        action_data = self._extract_json(full_response)
        if not action_data:
            return None

        result = self.actions.execute(action_data)

        # Chat fallback — LLM said something conversational
        if result and result.startswith("CHAT_FALLBACK::"):
            chat_text = result.split("::", 1)[1]
            self.audio.stop_thinking_sound()
            self.display.set_state(
                BotStates.SPEAKING, "Speaking...", cam_path=img_path)
            self.display.append_text("BOT: ", newline=False)
            self.display.append_text(chat_text, newline=True)
            self.audio.enqueue_tts(chat_text)
            self.memory["session"].append(
                {"role": "assistant", "content": chat_text})
            self.audio.wait_for_tts()
            self._end_response(chat_text)
            return True

        # Image capture → re-enter chat with vision
        if result == "IMAGE_CAPTURE_TRIGGERED":
            new_img = capture_image()
            if new_img:
                self.handle(user_text, img_path=new_img)
            return True

        # Show camera → display image, stay in CAMERA mode
        if result == "SHOW_CAMERA_TRIGGERED":
            new_img = capture_image()
            if new_img:
                self.audio.stop_thinking_sound()
                self.display.set_state(
                    BotStates.CAMERA, "Camera mode", cam_path=new_img)
                self.display.set_state(
                    BotStates.SPEAKING, "Looking...", cam_path=new_img)
                self.display.append_text("BOT: ", newline=False)
                msg = "Here's the camera view!"
                self.display.append_text(msg, newline=True)
                self.audio.enqueue_tts(msg)
                self.audio.wait_for_tts()
                self.display.set_state(
                    BotStates.CAMERA, "Camera mode", cam_path=new_img)
            return True

        # Fallback messages
        fallback_map = {
            "INVALID_ACTION": "I am not sure how to do that.",
            "SEARCH_EMPTY": "I searched, but I couldn't find any news about that.",
            "SEARCH_ERROR": "I cannot reach the internet right now.",
        }
        if result in fallback_map:
            text = fallback_map[result]
            self.audio.stop_thinking_sound()
            self.display.set_state(
                BotStates.SPEAKING, "Speaking...", cam_path=img_path)
            self.display.append_text("BOT: ", newline=False)
            self.display.append_text(text, newline=True)
            self.audio.enqueue_tts(text)
            return True

        if result and result.startswith("WEATHER_UNAVAILABLE::"):
            city = result.split("::", 1)[1]
            text = f"I could not get the weather for {city} right now."
            self.audio.stop_thinking_sound()
            self.display.set_state(
                BotStates.SPEAKING, "Speaking...", cam_path=img_path)
            self.display.append_text("BOT: ", newline=False)
            self.display.append_text(text, newline=True)
            self.audio.enqueue_tts(text)
            return True

        # General tool result → summarize via LLM
        if result:
            model = VISION_MODEL if img_path else TEXT_MODEL
            summary_prompt = [
                {"role": "system",
                 "content": "Summarize this result in one short sentence."},
                {"role": "user",
                 "content": f"RESULT: {result}\nUser Question: {user_text}"},
            ]
            self.display.set_state(BotStates.THINKING, "Reading...")
            self.audio.start_thinking_sound()

            final_resp = ollama.chat(
                model=model, messages=summary_prompt,
                stream=False, options=OLLAMA_OPTIONS)
            final_text = final_resp['message']['content']

            self.audio.stop_thinking_sound()
            self.display.set_state(
                BotStates.SPEAKING, "Speaking...", cam_path=img_path)
            self.display.append_text("BOT: ", newline=False)
            self.display.append_text(final_text, newline=True)
            self.audio.enqueue_tts(final_text)
            self.memory["session"].append(
                {"role": "assistant", "content": final_text})
            return True

        return None

    def _end_response(self, response_text):
        """Log response, show end face, return to idle."""
        logger.info(
            f"LLM: \"{response_text[:200]}"
            f"{'...' if len(response_text) > 200 else ''}\"")

        if (self.actions.pending_end_face
                and self.actions.pending_end_face in self.display.animations):
            end_face = self.actions.pending_end_face
            logger.info(f"END FACE (who): {end_face}")
            self.actions.pending_end_face = None
        else:
            end_faces = ["feliz", "sonrisa", "guino", "beso", "fiesta",
                         "risueno", "antenas", "corazon"]
            candidates = [f for f in end_faces if f in self.display.animations]
            end_face = random.choice(candidates) if candidates else BotStates.DORMIDO
            logger.info(f"END FACE (random): {end_face}")

        self.display.set_state(end_face, "Done!")
        # Block until display time elapses so main loop doesn't override the face
        deadline = time.time() + 5
        while time.time() < deadline:
            self.display.master.update()
            time.sleep(0.05)
        self.display.set_state(BotStates.IDLE, "Ready")

    @staticmethod
    def _extract_json(text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                import json
                return json.loads(match.group(0))
            return None
        except Exception:
            return None
