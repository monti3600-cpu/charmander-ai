import time
import threading
import numpy as np
import sounddevice as sd
import webrtcvad
import scipy.signal
from faster_whisper import WhisperModel

# =========================
# AUDIO CONFIG
# =========================

INPUT_DEVICE = 1
INPUT_RATE = 48000
TARGET_RATE = 16000
CHANNELS = 1

FRAME_MS = 20
FRAME_SIZE = int(TARGET_RATE * FRAME_MS / 1000)

# =========================
# TUNING
# =========================

SILENCE_TIMEOUT = 1
MAX_SPEECH_SEC = 6.0
MIN_RMS = 0.01
COOLDOWN_SEC = 0.5

# LED
LED_FLOOR = 0.005
LED_SCALE = 0.12

BAD_PHRASES = [
    "amara.org",
    "napisy stworzone",
    "subtitles",
    "thanks for watching",
    "dziękujemy za oglądanie",
    "zobacz, jak to się stało",
    "dzień dobry"
]


class StreamingSTT:
    def __init__(self, on_text, on_level=None):
        self.on_text = on_text
        self.on_level = on_level

        self.vad = webrtcvad.Vad(1)
        self.model = WhisperModel("small", compute_type="int8")

        self.listening = False
        self.paused = False
        self.is_speaking = False
        self.block_input = False  # 🔒 KLUCZOWA BLOKADA

        self.last_voice = 0.0
        self.speech_start = 0.0
        self.cooldown_until = 0.0

        self.audio_buf = np.zeros((0, 1), dtype=np.float32)
        self.speech_buf = []

        self.level_ema = 0.0
        self.last_text = ""
        self.last_text_time = 0.0

    # =========================

    def toggle(self):
        self.listening = not self.listening
        self._reset()
        return self.listening

    def pause(self, value: bool):
        self.paused = value
        if value:
            self._reset()

    def start(self):
        self.stream = sd.InputStream(
            device=INPUT_DEVICE,
            samplerate=INPUT_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._callback
        )
        self.stream.start()

    # =========================

    def _callback(self, indata, frames, time_info, status):
        # 🔇 TWARDY MUTE
        if self.block_input or self.paused or not self.listening:
            return

        now = time.time()
        if now < self.cooldown_until:
            return

        # stereo → mono
        if indata.ndim == 2 and indata.shape[1] == 2:
            indata = indata.mean(axis=1)

        # resample 48k → 16k
        indata = scipy.signal.resample_poly(
            indata,
            up=TARGET_RATE,
            down=INPUT_RATE
        ).reshape(-1, 1)

        indata = np.clip(indata * 1.3, -1.0, 1.0)
        self.audio_buf = np.vstack([self.audio_buf, indata])

        while len(self.audio_buf) >= FRAME_SIZE:
            frame = self.audio_buf[:FRAME_SIZE]
            self.audio_buf = self.audio_buf[FRAME_SIZE:]

            rms = float(np.sqrt(np.mean(frame ** 2)))

            # ---------- LED ----------
            led_rms = max(0.0, rms - LED_FLOOR)
            raw_level = min(led_rms / LED_SCALE, 1.0)

            self.level_ema = (
                0.6 * self.level_ema + 0.4 * raw_level
                if raw_level > self.level_ema
                else 0.9 * self.level_ema
            )

            if self.on_level:
                self.on_level(self.level_ema)

            # ---------- STT ----------
            pcm16 = (frame * 32767).astype(np.int16).tobytes()
            has_voice = self.vad.is_speech(pcm16, TARGET_RATE)

            if has_voice:
                if not self.is_speaking:
                    self.is_speaking = True
                    self.speech_start = now

                self.last_voice = now
                self.speech_buf.append(frame.copy())

            elif self.is_speaking and (
                now - self.last_voice > SILENCE_TIMEOUT
                or now - self.speech_start > MAX_SPEECH_SEC
            ):
                self.is_speaking = False

                if not self.speech_buf:
                    return

                audio = np.concatenate(self.speech_buf, axis=0)
                self.speech_buf.clear()

                # 🔒 BLOKUJEMY MIKROFON NATYCHMIAST
                self.block_input = True

                self.cooldown_until = time.time() + COOLDOWN_SEC

                threading.Thread(
                    target=self._transcribe,
                    args=(audio,),
                    daemon=True
                ).start()

    # =========================

    def _transcribe(self, audio):
        if float(np.sqrt(np.mean(audio ** 2))) < MIN_RMS:
            self.block_input = False
            return

        segments, _ = self.model.transcribe(
            audio.flatten(),
            language="pl",
            temperature=0.0,
            beam_size=5
        )

        text = " ".join(s.text for s in segments).strip()
        if not text:
            self.block_input = False
            return

        lower = text.lower()
        if any(bad in lower for bad in BAD_PHRASES):
            print("⚠️ ignored:", text)
            self.block_input = False
            return

        now = time.time()
        if text == self.last_text and now - self.last_text_time < 3.0:
            self.block_input = False
            return

        self.last_text = text
        self.last_text_time = now

        self.on_text(text)

        # 🔓 ODBLOKUJ MIKROFON PO CAŁYM CYKLU
        self.block_input = False

    # =========================

    def _reset(self):
        self.audio_buf = np.zeros((0, 1), dtype=np.float32)
        self.speech_buf.clear()
        self.is_speaking = False
        self.level_ema = 0.0
        self.last_voice = 0.0
        self.speech_start = 0.0
        self.cooldown_until = 0.0
        self.block_input = False
