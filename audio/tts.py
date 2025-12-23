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

        # 1️⃣ Podstawowy TTS (PL) — NORMALNY poziom głośności
        subprocess.run(
            [
                "espeak-ng",
                "-v", "pl",
                "-s", "200",     # żywy
                "-p", "150",     # wyższy pitch
                "-a", "50",      # głośniej
                "-w", raw.name,
                text
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 2️⃣ Charmander FX 🔥 (bez przesteru)
        subprocess.run(
            [
                "sox", raw.name, fx.name,
                "pitch", "400",       # wyższy, młodszy głos
                "overdrive", "1.5",   # delikatna chropowatość 
                "treble", "2",        # jaśniej
                "tempo", "1.10"       # żwawszy
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

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

        subprocess.run(
            ["aplay", fx.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if mouth_leds:
            mouth_leds.stop()

        time.sleep(0.03)
