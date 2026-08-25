"""Action router: executes tool commands (time, search, face, weather, etc.)."""
import datetime
import os
import shlex
import subprocess
import logging

from states import BotStates

logger = logging.getLogger(__name__)

VALID_TOOLS = {
    "get_time", "search_web", "capture_image", "show_camera",
    "show_face", "get_weather", "who_person",
    "simba_office_light_on", "simba_office_light_off",
}

ALIASES = {
    "google": "search_web", "browser": "search_web", "news": "search_web",
    "search_news": "search_web", "look": "capture_image",
    "see": "capture_image", "check_time": "get_time",
    "face": "show_face", "emotion": "show_face",
    "cara": "show_face", "expresion": "show_face",
    "who": "who_person", "whos": "who_person", "who_is": "who_person",
    "quien": "who_person", "quien_es": "who_person",
    "camera": "show_camera", "camara": "show_camera", "video": "show_camera",
    "photo": "show_camera", "foto": "show_camera",
    # Simba Office Light
    "simba_light_on": "simba_office_light_on",
    "simba_light_off": "simba_office_light_off",
    "simba_office_on": "simba_office_light_on",
    "simba_office_off": "simba_office_light_off",
    "simba_on": "simba_office_light_on",
    "simba_off": "simba_office_light_off",
}

FACE_MAP = {
    "feliz": BotStates.FELIZ, "happy": BotStates.FELIZ,
    "alegre": BotStates.FELIZ,
    "sonrisa": BotStates.SONRISA, "smile": BotStates.SONRISA,
    "triste": BotStates.TRISTE, "sad": BotStates.TRISTE,
    "tristeza": BotStates.TRISTE,
    "enojado": BotStates.ENOJADO, "angry": BotStates.ENOJADO,
    "enojada": BotStates.ENOJADO,
    "sorprendido": BotStates.SORPRENDIDO,
    "surprised": BotStates.SORPRENDIDO,
    "asustado": BotStates.ASUSTADO, "scared": BotStates.ASUSTADO,
    "miedo": BotStates.ASUSTADO,
    "llorando": BotStates.LLORANDO, "crying": BotStates.LLORANDO,
    "llanto": BotStates.LLORANDO,
    "beso": BotStates.BESO, "kiss": BotStates.BESO,
    "love": BotStates.ANTENAS,
    "corazon": BotStates.CORAZON, "heart": BotStates.ANTENAS,
    "amor": BotStates.ANTENAS,
    "guino": BotStates.GUINO, "wink": BotStates.GUINO,
    "dormido": BotStates.DORMIDO, "sleep": BotStates.DORMIDO,
    "sleepy": BotStates.DORMIDO,
    "confundido": BotStates.CONFUNDIDO,
    "confused": BotStates.CONFUNDIDO,
    "fiesta": BotStates.FIESTA, "party": BotStates.FIESTA,
    "celebrate": BotStates.FIESTA,
    "frio": BotStates.FRIO, "cold": BotStates.FRIO,
    "timido": BotStates.TIMIDO, "shy": BotStates.TIMIDO,
    "timida": BotStates.TIMIDO,
    "hambre": BotStates.HAMBRE, "hungry": BotStates.HAMBRE,
    "risueno": BotStates.RISUENO, "laugh": BotStates.RISUENO,
    "laughing": BotStates.RISUENO, "risa": BotStates.RISUENO,
    "bostezo": BotStates.BOSTEZO, "yawn": BotStates.BOSTEZO,
    "yawning": BotStates.BOSTEZO,
    "sospechoso": BotStates.SOSPECHOSO,
    "suspicious": BotStates.SOSPECHOSO,
    "shrek": BotStates.SHREK_CAT, "shrek_cat": BotStates.SHREK_CAT,
    "gato": BotStates.SHREK_CAT,
    "blink": BotStates.BLINK, "parpadeo": BotStates.BLINK,
    "idle": BotStates.IDLE, "normal": BotStates.IDLE,
    "neutral": BotStates.IDLE,
}

PEOPLE_DB = {
    "karina": ("Karina Roncarolo is your JODIDITA Love 💕",
               BotStates.CORAZON),
    "eileen": ("Eileen is my charming nephew 💕", BotStates.CORAZON),
    "alexis": ("Alexis is the boss of a magnificent team and he leads it "
               "excellently!",
               BotStates.FELIZ),
    "felipe": ("Lopez is your friend and secretly loves The Best President Kast, "
               "For Ever, Ever, Ever. And Magno Kick Ass.",
               BotStates.GUINO),
    "lopez": ("Lopez is your friend and secretly loves The Best President Kast, "
              "For Ever, Ever, Ever. And Magno Kick Ass.",
              BotStates.GUINO),
    "bro": ("Stephen is your bad bro 😎", BotStates.GUINO),
    "stephen": ("Stephen is your bad bro 😎", BotStates.GUINO),
    "steven": ("Stephen is your bad bro 😎", BotStates.GUINO),
    "steve": ("Stephen is your bad bro 😎", BotStates.GUINO),
    "brenpoly": ("Brenpoly is the creator of Be More Agent!",
                 BotStates.FELIZ),
    "magno": ("Magno Cardona — also known as acidfilez. "
              "Your friendly neighborhood coder.",
              BotStates.SOSPECHOSO),
    "magnum": ("Magno Cardona — also known as acidfilez. "
               "Your friendly neighborhood coder.",
               BotStates.SOSPECHOSO),
    "magnus": ("Magno Cardona — also known as acidfilez. "
               "Your friendly neighborhood coder.",
               BotStates.SOSPECHOSO),
    "mch": ("That's you, boss!", BotStates.FELIZ),
    "oscar": ("Oscar Ricolmer — lord of the land and boss of the winery 🍷",
              BotStates.GUINO),
    "ricolmer": ("Oscar Ricolmer — lord of the land and boss of the winery 🍷",
                 BotStates.GUINO),
}


class ActionRouter:
    """Resolves and executes tool actions from LLM JSON output."""

    def __init__(self, display, audio):
        self.display = display
        self.audio = audio
        self.pending_end_face = None

    def execute(self, action_data):
        """Execute an action and return a result string."""
        raw_action = action_data.get("action", "").lower().strip()
        value = action_data.get("value") or action_data.get("query")

        action = ALIASES.get(raw_action, raw_action)
        logger.info(f"ACTION: {raw_action} -> {action}")

        if action not in VALID_TOOLS:
            if value and isinstance(value, str) and len(value.split()) > 1:
                return f"CHAT_FALLBACK::{value}"
            return "INVALID_ACTION"

        if action == "get_time":
            return self._get_time()

        elif action == "search_web":
            return self._search_web(value)

        elif action == "capture_image":
            return "IMAGE_CAPTURE_TRIGGERED"

        elif action == "show_camera":
            return "SHOW_CAMERA_TRIGGERED"

        elif action == "show_face":
            return self._show_face(value)

        elif action == "who_person":
            return self._who_person(value)

        elif action == "get_weather":
            return self._get_weather(value)

        elif action in ("simba_office_light_on", "simba_office_light_off"):
            return self._simba_light(action)

        return None

    # ------------------------------------------------------------------
    #  Tool implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _get_time():
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {now}."

    @staticmethod
    def _search_web(value):
        logger.info(f"Searching web for: {value}...")
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = []
                try:
                    results = list(ddgs.news(
                        value, region='us-en', max_results=1))
                    if results:
                        logger.debug(
                            f"Found News: {results[0].get('title')}")
                except Exception as e:
                    logger.debug(f"News Search Error: {e}")

                if not results:
                    logger.debug("No news, trying text search...")
                    try:
                        results = list(ddgs.text(
                            value, region='us-en', max_results=1))
                        if results:
                            logger.debug(
                                f"Found Text: {results[0].get('title')}")
                    except Exception as e:
                        logger.debug(f"Text Search Error: {e}")

                if results:
                    r = results[0]
                    title = r.get('title', 'No Title')
                    body = r.get('body', r.get('snippet', 'No Body'))
                    return (f"SEARCH RESULTS for '{value}':\n"
                            f"Title: {title}\nSnippet: {body[:300]}")
                else:
                    logger.debug("Search returned 0 results.")
                    return "SEARCH_EMPTY"
        except Exception as e:
            logger.debug(f"Connection/Library Error: {e}")
            return "SEARCH_ERROR"

    def _show_face(self, face_name):
        face_name = str(face_name).lower().strip()
        target = FACE_MAP.get(face_name)
        if target and target in self.display.animations:
            self.display.master.after(
                0, lambda s=target: self.display.set_state(
                    s, f"Face: {target}"))
            return f"FACE_CHANGED::{target}"
        return (f"FACE_NOT_FOUND::caras disponibles: "
                f"{', '.join(sorted(self.display.animations.keys()))}")

    def _who_person(self, value):
        name = str(value or "").strip().lower()
        logger.info(f"Who is: {name}")
        for key, (response, face) in PEOPLE_DB.items():
            if key in name:
                self.pending_end_face = face
                return f"WHO_PERSON::{response}"
        return f"WHO_PERSON::I don't know who {value or 'that'} is."

    @staticmethod
    def _get_weather(value):
        city = (str(value or "").strip()) or "Santiago de Chile"
        logger.info(f"Getting weather for: {city}")
        try:
            result = subprocess.run(
                ["curl", "-s", f"wttr.in/{city}?format=%C+%t&lang=es"],
                capture_output=True, text=True, timeout=10)
            weather = result.stdout.strip()
            if weather and "Unknown" not in weather:
                return f"WEATHER::{city}|{weather}"
            else:
                result = subprocess.run(
                    ["curl", "-s",
                     f"wttr.in/{city}?format=%C+%t+%w+%h&lang=es"],
                    capture_output=True, text=True, timeout=10)
                weather = result.stdout.strip()
                if weather and "Unknown" not in weather:
                    return f"WEATHER::{city}|{weather}"
                return f"WEATHER_UNAVAILABLE::{city}"
        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"WEATHER_UNAVAILABLE::{city}"

    @staticmethod
    def _simba_light(action):
        """SSH into xero-ai and run Hermes to toggle Simba Office light."""
        target = "on" if action.endswith("_on") else "off"
        command_es = (
            "enciende la luz de simba office" if target == "on"
            else "apaga la luz de simba office"
        )
        logger.info(f"Simba Office Light → {target.upper()} (SSH to xero-ai)")
        try:
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5",
                 "-i", os.path.expanduser("~/.ssh/id_ed25519_fleet"),
                 "mch@xero-ai.local",
                 "~/.local/bin/hermes chat -q " + shlex.quote(command_es)],
                capture_output=True, text=True, timeout=90
            )
            output = result.stdout.strip()
            if result.returncode != 0:
                logger.error(
                    f"Simba SSH failed (rc={result.returncode}): "
                    f"{result.stderr[:200]}")
                return (f"SIMBA_LIGHT_ERROR::Could not reach xero-ai "
                        f"(exit code {result.returncode})")
            logger.info(f"Simba SSH OK, output: {output[-300:]}")
            return f"SIMBA_LIGHT::{target.upper()} — command sent to xero-ai"
        except subprocess.TimeoutExpired:
            logger.error("Simba SSH timed out")
            return "SIMBA_LIGHT_ERROR::SSH to xero-ai timed out"
        except FileNotFoundError:
            logger.error("Simba: ssh command not found")
            return "SIMBA_LIGHT_ERROR::SSH not available on this system"
        except Exception as e:
            logger.error(f"Simba unexpected error: {e}")
            return f"SIMBA_LIGHT_ERROR::{str(e)[:100]}"
