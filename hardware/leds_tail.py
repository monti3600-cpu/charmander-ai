import os
from gpiozero import PWMLED

if os.getenv("GPIOZERO_PIN_FACTORY") is None:
    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"


class TailLeds:
    def __init__(self, pins):
        self.leds = [PWMLED(p, active_high=False, initial_value=0.0) for p in pins]
        self.off()

    def set_level(self, level):
        for led in self.leds:
            led.value = level

    def off(self):
        for led in self.leds:
            led.value = 0.0
