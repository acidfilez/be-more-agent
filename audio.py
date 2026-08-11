"""Audio subsystem: wake word, recording, transcription, TTS, sound FX."""
import threading
import time
import re
import os
import wave
import random
import subprocess
import select
import sys
import logging

import numpy as np
import sounddevice as sd
import scipy.signal

from config import (
    WAKE_WORD_MODEL, WAKE_WORD_THRESHOLD, CURRENT_CONFIG,
    INPUT_DEVICE_NAME, choose_input_samplerate, TEXT_MODEL, OLLAMA_OPTIONS,
)
from states import BotStates

logger = logging.getLogger(__name__)

# Sound directories
GREETING_SOUNDS_DIR = "sounds/greeting_sounds"
ACK_SOUNDS_DIR = "sounds/ack_sounds"
THINKING_SOUNDS_DIR = "sounds/thinking_sounds"
ERROR_SOUNDS_DIR = "sounds/error_sounds"


class AudioManager:
    """Manages all audio I/O: wake word detection, recording, transcription,
    TTS output, and sound FX playback."""

    def __init__(self, state_callback, pump_callback=None):
        """
        Args:
            state_callback: callable(state, message, cam_path) to notify
                            the display/GUI of state changes.
            pump_callback: optional callable() to pump the GUI event loop
                           during blocking I/O (e.g. tkinter master.update).
        """
        self._state_cb = state_callback
        self._pump_cb = pump_callback

        # Wake word
        self.oww_model = None
        try:
            from openwakeword.model import Model
            self.oww_model = Model(wakeword_models=[WAKE_WORD_MODEL],
                                   inference_framework="onnx")
            logger.info(f"Wake word loaded — model: {WAKE_WORD_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load wake word model: {e}")

        # PTT / recording state
        self.recording_active = threading.Event()
        self.ptt_event = threading.Event()
        self.last_ptt_time = 0

        # Interrupt
        self.interrupted = threading.Event()

        # TTS
        self.tts_queue = []
        self.tts_queue_lock = threading.Lock()
        self.tts_thread = None
        self.tts_active = threading.Event()
        self.current_audio_process = None
        self.current_volume = 0

        # Thinking sound
        self.thinking_sound_active = threading.Event()

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def start_tts_worker(self):
        self.tts_active.set()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def stop(self):
        self.interrupted.set()
        self.thinking_sound_active.clear()
        self.recording_active.clear()
        with self.tts_queue_lock:
            self.tts_queue.clear()
        if self.current_audio_process:
            try:
                self.current_audio_process.terminate()
                self.current_audio_process.wait(timeout=1)
            except Exception:
                pass
        self.tts_active.clear()
        try:
            sd.stop()
        except Exception:
            pass

    def warm_up(self):
        """Pre-load Ollama model."""
        self._state_cb(BotStates.WARMUP, "Warming up brains...")
        import ollama
        try:
            ollama.generate(model=TEXT_MODEL, prompt="", keep_alive=-1)
        except Exception as e:
            logger.error(f"Failed to load {TEXT_MODEL}: {e}")
        self._play_sound_file(self._get_random_sound(GREETING_SOUNDS_DIR))
        if self.oww_model:
            self.oww_model.reset()
        time.sleep(0.5)
        logger.info("Models loaded, ready to go!")

    def detect_wake_word_or_ptt(self):
        self._state_cb(BotStates.IDLE, "Waiting...")
        self.ptt_event.clear()

        if self.oww_model:
            self.oww_model.reset()

        if self.oww_model is None:
            self.ptt_event.wait()
            self.ptt_event.clear()
            return "PTT"

        CHUNK_SIZE = 1280
        OWW_SAMPLE_RATE = 16000

        input_rate = choose_input_samplerate(
            INPUT_DEVICE_NAME, CURRENT_CONFIG.get("input_sample_rate"))
        use_resampling = (input_rate != OWW_SAMPLE_RATE)
        input_chunk_size = (int(CHUNK_SIZE * (input_rate / OWW_SAMPLE_RATE))
                            if use_resampling else CHUNK_SIZE)

        stream_args = {
            "samplerate": input_rate,
            "channels": 1,
            "dtype": 'int16',
            "blocksize": input_chunk_size,
            "device": INPUT_DEVICE_NAME,
        }

        try:
            self._listen_loop(stream_args, input_chunk_size,
                              CHUNK_SIZE, use_resampling)
        except StopIteration as si:
            return str(si)
        except Exception as e:
            logger.warning(f"Stream failed with defaults: {e}. Retrying...")
            try:
                stream_args["blocksize"] = 1024
                use_resampling = True
                self._listen_loop(stream_args, 1024, CHUNK_SIZE, use_resampling)
            except StopIteration as si:
                return str(si)
            except Exception as e2:
                logger.error(f"Wake Word Stream Error: {e2}")
                self.ptt_event.wait()
                return "PTT"

        return "WAKE"

    def record_voice_adaptive(self, filename="input.wav"):
        logger.info("Recording started (adaptive mode)")
        time.sleep(0.5)
        samplerate = choose_input_samplerate(
            INPUT_DEVICE_NAME, CURRENT_CONFIG.get("input_sample_rate"))

        silence_threshold = 0.02
        silence_duration = 2.0
        max_record_time = 30.0
        buffer = []
        silent_chunks = 0
        chunk_duration = 0.05
        chunk_size = int(samplerate * chunk_duration)

        num_silent_chunks = int(silence_duration / chunk_duration)
        max_chunks = int(max_record_time / chunk_duration)
        recorded_chunks = 0
        silence_started = False

        def callback(indata, frames, time_info, status):
            nonlocal silent_chunks, recorded_chunks, silence_started
            volume_norm = np.linalg.norm(indata) / np.sqrt(len(indata))
            buffer.append(indata.copy())
            recorded_chunks += 1
            if recorded_chunks < 5:
                return
            if recorded_chunks % 50 == 0:
                logger.debug(
                    f"chunk {recorded_chunks}: volume={volume_norm:.5f}, "
                    f"silent_chunks={silent_chunks}")
            if volume_norm < silence_threshold:
                silent_chunks += 1
                if silent_chunks >= num_silent_chunks:
                    silence_started = True
            else:
                silent_chunks = 0

        try:
            sd.stop()
            time.sleep(0.2)
            with sd.InputStream(samplerate=samplerate, channels=1,
                                callback=callback, device=INPUT_DEVICE_NAME,
                                blocksize=chunk_size):
                while not silence_started and recorded_chunks < max_chunks:
                    sd.sleep(int(chunk_duration * 1000))
        except Exception as e:
            logger.error(f"Adaptive recording failed: {e}")
            return None

        logger.info(f"Recording finished, saved to {filename} @ {samplerate}Hz")
        return self._save_audio_buffer(buffer, filename, samplerate)

    def record_voice_ptt(self, filename="input.wav"):
        logger.info("Recording started (PTT mode)")
        time.sleep(0.5)
        samplerate = choose_input_samplerate(
            INPUT_DEVICE_NAME, CURRENT_CONFIG.get("input_sample_rate"))

        buffer = []

        def callback(indata, frames, time_info, status):
            buffer.append(indata.copy())

        try:
            sd.stop()
            time.sleep(0.2)
            with sd.InputStream(samplerate=samplerate, channels=1,
                                callback=callback, device=INPUT_DEVICE_NAME):
                while self.recording_active.is_set():
                    sd.sleep(50)
        except Exception as e:
            logger.error(f"PTT recording failed: {e}")
            return None

        return self._save_audio_buffer(buffer, filename, samplerate)

    def transcribe_audio(self, filename):
        logger.info("Transcribing...")
        try:
            result = subprocess.run(
                ["./whisper.cpp/build/bin/whisper-cli", "-m",
                 "./whisper.cpp/models/ggml-base.en.bin", "-l", "en",
                 "-t", "4", "-f", filename],
                capture_output=True, text=True
            )
            lines = result.stdout.strip().split('\n')
            if lines and lines[-1].strip():
                last_line = lines[-1].strip()
                transcription = (last_line.split("]")[1].strip()
                                 if ']' in last_line else last_line)
            else:
                transcription = ""
            logger.info(f"Heard: '{transcription}'")
            return transcription.strip()
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def start_thinking_sound(self):
        self.thinking_sound_active.set()
        threading.Thread(target=self._thinking_loop, daemon=True).start()

    def stop_thinking_sound(self):
        self.thinking_sound_active.clear()

    def enqueue_tts(self, text):
        with self.tts_queue_lock:
            self.tts_queue.append(text)

    def wait_for_tts(self):
        while self.tts_queue or self.tts_active.is_set():
            if self.interrupted.is_set():
                break
            time.sleep(0.1)

    def handle_ptt_toggle(self, current_state_text):
        current_time = time.time()
        if current_time - self.last_ptt_time < 0.5:
            return
        self.last_ptt_time = current_time

        if self.recording_active.is_set():
            logger.info("[PTT] Toggle OFF")
            self.recording_active.clear()
        else:
            if "Wait" in current_state_text:
                logger.info("[PTT] Toggle ON")
                self.recording_active.set()
                self.ptt_event.set()

    def handle_interrupt(self):
        self.interrupted.set()
        self.thinking_sound_active.clear()
        with self.tts_queue_lock:
            self.tts_queue.clear()
        if self.current_audio_process:
            try:
                self.current_audio_process.terminate()
            except Exception:
                pass

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _listen_loop(self, stream_args, input_chunk_size,
                     target_chunk_size, use_resampling):
        with sd.InputStream(**stream_args) as stream:
            logger.info(
                f"Listening with rate {stream_args['samplerate']} "
                f"and block {stream_args['blocksize']}")
            tick = 0
            while True:
                if self.ptt_event.is_set():
                    self.ptt_event.clear()
                    raise StopIteration("PTT")

                if sys.stdin.isatty():
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.001)
                    if rlist:
                        sys.stdin.readline()
                        raise StopIteration("CLI")

                read_size = input_chunk_size
                if stream_args.get('blocksize') == 0:
                    read_size = 1024

                try:
                    data, overflow = stream.read(read_size)
                    if overflow:
                        logger.warning("Audio buffer overflow!")
                        raise RuntimeError("Audio Buffer Overflow")
                except Exception as e:
                    raise RuntimeError(f"Audio read failed: {e}")

                audio_data = np.frombuffer(data, dtype=np.int16)
                if audio_data.ndim > 1:
                    audio_data = audio_data.flatten()

                # Pump GUI event loop so animations/scheduled callbacks run
                tick += 1
                if self._pump_cb and tick % 10 == 0:
                    self._pump_cb()

                if use_resampling:
                    step = len(audio_data) / target_chunk_size
                    indices = np.arange(
                        0, len(audio_data), step)[:target_chunk_size].astype(int)
                    audio_data = audio_data[indices]

                current_max = np.max(np.abs(audio_data))
                if current_max > 200:
                    prediction = self.oww_model.predict(audio_data)
                    for mdl in self.oww_model.prediction_buffer.keys():
                        score = list(self.oww_model.prediction_buffer[mdl])[-1]
                        if score > WAKE_WORD_THRESHOLD:
                            logger.info(f"Wake word triggered! score={score:.2f}")
                            self.oww_model.reset()
                            return

    def _save_audio_buffer(self, buffer, filename, samplerate=16000):
        if not buffer:
            return None
        audio_data = np.concatenate(buffer, axis=0).flatten()
        audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=0.0, neginf=0.0)
        audio_data = (audio_data * 32767).astype(np.int16)
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio_data.tobytes())
        self._play_sound_file(self._get_random_sound(ACK_SOUNDS_DIR))
        return filename

    # --- TTS ---

    def _tts_worker(self):
        while True:
            text = None
            with self.tts_queue_lock:
                if self.tts_queue:
                    text = self.tts_queue.pop(0)
                    self.tts_active.set()
            if text:
                self._speak(text)
                self.tts_active.clear()
            else:
                time.sleep(0.05)

    def _speak(self, text):
        clean = re.sub(r"[^\w\s,.!?:-]", "", text)
        if not clean.strip():
            return

        logger.info(f"Piper TTS: '{clean}'")
        voice_model = CURRENT_CONFIG.get(
            "voice_model", "piper/en_GB-semaine-medium.onnx")

        try:
            self.current_audio_process = subprocess.Popen(
                ["./piper/piper", "--model", voice_model, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self.current_audio_process.stdin.write(clean.encode() + b'\n')
            self.current_audio_process.stdin.close()

            try:
                device_info = sd.query_devices(kind='output')
                native_rate = int(device_info['default_samplerate'])
            except Exception:
                native_rate = 48000

            PIPER_RATE = 22050
            use_native_rate = False
            try:
                sd.check_output_settings(device=None, samplerate=PIPER_RATE)
            except Exception:
                use_native_rate = True

            with sd.RawOutputStream(
                samplerate=native_rate if use_native_rate else PIPER_RATE,
                channels=1, dtype='int16', device=None,
                latency='low', blocksize=2048
            ) as stream:
                while True:
                    if self.interrupted.is_set():
                        break
                    data = self.current_audio_process.stdout.read(4096)
                    if not data:
                        break
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    if len(audio_chunk) > 0:
                        self.current_volume = np.max(np.abs(audio_chunk))
                        if use_native_rate:
                            num_samples = int(
                                len(audio_chunk) * (native_rate / PIPER_RATE))
                            audio_chunk = scipy.signal.resample(
                                audio_chunk, num_samples).astype(np.int16)
                        stream.write(audio_chunk.tobytes())
                    else:
                        self.current_volume = 0
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Audio error: {e}")
        finally:
            self.current_volume = 0
            if self.current_audio_process:
                if self.current_audio_process.stdout:
                    self.current_audio_process.stdout.close()
                if self.current_audio_process.poll() is None:
                    self.current_audio_process.terminate()
                self.current_audio_process = None

    # --- Thinking sound ---

    def _thinking_loop(self):
        time.sleep(0.5)
        while self.thinking_sound_active.is_set():
            sound = self._get_random_sound(THINKING_SOUNDS_DIR)
            if sound:
                self._play_sound_file(sound)
            for _ in range(50):
                if not self.thinking_sound_active.is_set():
                    return
                time.sleep(0.1)

    # --- Sound FX ---

    @staticmethod
    def _get_random_sound(directory):
        if os.path.exists(directory):
            files = [f for f in os.listdir(directory) if f.endswith(".wav")]
            return os.path.join(directory, random.choice(files)) if files else None
        return None

    @staticmethod
    def _play_sound_file(file_path):
        if not file_path or not os.path.exists(file_path):
            return
        try:
            with wave.open(file_path, 'rb') as wf:
                file_sr = wf.getframerate()
                data = wf.readframes(wf.getnframes())
                audio = np.frombuffer(data, dtype=np.int16)

            try:
                device_info = sd.query_devices(kind='output')
                native_rate = int(device_info['default_samplerate'])
            except Exception:
                native_rate = 48000

            playback_rate = file_sr
            try:
                sd.check_output_settings(device=None, samplerate=file_sr)
            except Exception:
                playback_rate = native_rate
                num_samples = int(len(audio) * (native_rate / file_sr))
                audio = scipy.signal.resample(
                    audio, num_samples).astype(np.int16)

            sd.play(audio, playback_rate)
            sd.wait()
        except Exception:
            pass
