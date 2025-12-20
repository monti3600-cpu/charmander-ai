import subprocess
import tempfile
import wave
import numpy as np
import time


def speak(text: str, mouth_leds):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run([
            "espeak-ng", "-v", "pl",
            "-s", "200",
            "-p", "400",
            "-w", f.name,
            text
        ], check=True)

        with wave.open(f.name, "rb") as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            data = data.astype(np.float32) / 32768.0

        step = 1024
        envelope = []
        for i in range(0, len(data), step):
            chunk = data[i:i + step]
            envelope.append(float(np.sqrt(np.mean(chunk ** 2))))

        maxv = max(envelope) if envelope else 1.0
        envelope = [min(v / maxv, 1.0) for v in envelope]

        mouth_leds.start(envelope)
        subprocess.run(["aplay", f.name], check=True)
        mouth_leds.stop()
