from gpiozero import Button


class ButtonController:
    def __init__(self, pin):
        self.button = Button(pin, bounce_time=0.2)
        self.on_press = None
        self.button.when_pressed = self._pressed

    def _pressed(self):
        if self.on_press:
            self.on_press()
