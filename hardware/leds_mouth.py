import time
import threading
import os
from gpiozero import PWMLED

if os.getenv("GPIOZERO_PIN_FACTORY") is None:
    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"


class MouthLeds:
    def __init__(self, pins):
        self.leds = [PWMLED(p, active_high=False, initial_value=0.0) for p in pins]
        self._stop = False

    def start(self, envelope, step_sec=0.03):
        self._stop = False

        def loop():
            for v in envelope:
                if self._stop:
                    break
                for led in self.leds:
                    led.value = v
                time.sleep(step_sec)
            self.off()

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self._stop = True
        self.off()

    def off(self):
        for led in self.leds:
            led.value = 0.0
