import subprocess
import tempfile
import wave
import numpy as np
import time


def speak(text: str, mouth_leds):
    if not text:
        return

    with tempfile.NamedTemporaryFile(suffix=".wav") as raw, \
         tempfile.NamedTemporaryFile(suffix=".wav") as fx:

        # 1️⃣ Podstawowy TTS (PL)
        subprocess.run([
            "espeak-ng",
            "-v", "pl",
            "-s", "145",     # szybciej = bardziej żywy
            "-p", "70",      # wyższy pitch
            "-a", "180",     # głośniej
            "-w", raw.name,
            text
        ], check=True)

        # 2️⃣ Charmander FX 🔥 (lekko, bez przesady)
        subprocess.run([
            "sox", raw.name, fx.name,
            "pitch", "220",        # wyższy, młodszy głos
            "overdrive", "4",      # delikatna chropowatość
            "treble", "5",         # jaśniej
            "tempo", "1.05"        # żwawszy
        ], check=True)

        # 3️⃣ Envelope do pyska
        with wave.open(fx.name, "rb") as wf:
            data = np.frombuffer(
                wf.readframes(wf.getnframes()),
                dtype=np.int16
            ).astype(np.float32) / 32768.0

        step = 1024
        env = [
            float(np.sqrt(np.mean(data[i:i + step] ** 2)))
            for i in range(0, len(data), step)
        ]

        m = max(env) if env else 1.0
        env = [min(v / m, 1.0) for v in env]

        # 4️⃣ Mówienie + pyszczek
        if mouth_leds:
            mouth_leds.start(env)

        subprocess.run(["aplay", fx.name], check=True)

        if mouth_leds:
            mouth_leds.stop()

        time.sleep(0.03)
