import time
from datetime import datetime

from core.state import State
from audio.stt import StreamingSTT
from audio.tts import speak
from ai.chat import respond
from ai.memory import add
from hardware.leds_tail import TailLeds
from hardware.leds_mouth import MouthLeds
from hardware.buttons import ButtonController
from utils.config import *
from utils.log import sys, stt, gpt


# =========================
# GLOBAL STATE
# =========================

state = State()
mode = "Normalny"

tail = None
mouth = None
stt_engine = None


# =========================
# CALLBACKS
# =========================

def on_voice_level(level):
    if state.listening and not state.paused:
        tail.set_level(level)


def on_text(text):
    global state

    stt(text)
    state.last_interaction = datetime.now()

    reply = respond(text, mode, state)
    if not reply:
        return

    gpt(reply)
    add(text, reply)

    state.paused = True
    tail.off()
    speak(reply, mouth)
    state.paused = False


def toggle_listening():
    global state

    state.listening = stt_engine.toggle()
    msg = "Czar… słucham." if state.listening else "Dobra… idę spać."
    sys(msg)

    state.paused = True
    tail.off()
    speak(msg, mouth)
    state.paused = False


def belly_press():
    global mode, state

    modes = ["Normalny", "Laleczka Czaki", "Ziomek"]
    mode = modes[(modes.index(mode) + 1) % len(modes)]

    msg = f"Tryb: {mode}"
    sys(msg)

    state.paused = True
    tail.off()
    speak(msg, mouth)
    state.paused = False


# =========================
# MAIN
# =========================

def main():
    global tail, mouth, stt_engine

    sys("Charmander AI startuje 🔥")

    import subprocess

    subprocess.run(
        ["alsactl", "init"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # LED
    tail = TailLeds(TAIL_PINS)
    mouth = MouthLeds(MOUTH_PINS)

    # STT
    stt_engine = StreamingSTT(
        on_text=on_text,
        on_level=on_voice_level
    )
    stt_engine.start()

    # BUTTONS
    btn_left = ButtonController(PIN_LEFT)
    btn_belly = ButtonController(PIN_BELLY)

    btn_left.on_press = toggle_listening
    btn_belly.on_press = belly_press

    # LOOP
    while True:
        time.sleep(0.1)


if __name__ == "__main__":
    main()
