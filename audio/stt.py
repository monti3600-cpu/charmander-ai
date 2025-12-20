import time
import threading
import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
FRAME_MS = 20
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)
SILENCE_TIMEOUT = 1.0

MIN_RMS = 0.004
BAD_PHRASES = [
    "amara.org",
    "napisy stworzone",
    "subtitles",
    "thanks for watching",
    "dziękujemy za oglądanie"
]


class StreamingSTT:
    def __init__(self, on_text, on_level=None):
        self.on_text = on_text
        self.on_level = on_level

        self.vad = webrtcvad.Vad(2)
        self.model = WhisperModel("small", compute_type="int8")

        self.listening = False
        self.paused = False
        self.is_speaking = False
        self.last_voice = 0.0

        self.audio_buf = np.zeros((0, 1), dtype=np.float32)
        self.speech_buf = []

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
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback
        )
        self.stream.start()

    def _callback(self, indata, frames, time_info, status):
        if self.paused or not self.listening:
            return

        indata *= 1.5
        self.audio_buf = np.vstack([self.audio_buf, indata.copy()])

        while len(self.audio_buf) >= FRAME_SIZE:
            frame = self.audio_buf[:FRAME_SIZE]
            self.audio_buf = self.audio_buf[FRAME_SIZE:]

            rms = float(np.sqrt(np.mean(frame ** 2)))
            level = min(rms / 0.15, 1.0)
            if self.on_level:
                self.on_level(level)

            pcm16 = (frame * 32767).astype(np.int16).tobytes()
            has_voice = self.vad.is_speech(pcm16, SAMPLE_RATE)

            now = time.time()
            if has_voice:
                self.is_speaking = True
                self.last_voice = now
                self.speech_buf.append(frame.copy())

            elif self.is_speaking and now - self.last_voice > SILENCE_TIMEOUT:
                self.is_speaking = False
                audio = np.concatenate(self.speech_buf, axis=0)
                self.speech_buf.clear()
                threading.Thread(
                    target=self._transcribe,
                    args=(audio,),
                    daemon=True
                ).start()

    def _transcribe(self, audio):
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < MIN_RMS:
            return

        segments, _ = self.model.transcribe(
            audio.flatten(),
            language="pl",
            temperature=0.0,
            beam_size=5
        )

        text = " ".join(s.text for s in segments).strip()
        if not text:
            return

        lower = text.lower()
        if any(bad in lower for bad in BAD_PHRASES):
            print("⚠️ Ignored hallucination:", text)
            return

        self.on_text(text)

    def _reset(self):
        self.audio_buf = np.zeros((0, 1), dtype=np.float32)
        self.speech_buf.clear()
        self.is_speaking = False
