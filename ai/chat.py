from ai.modes import MODES
from ai.memory import recent
from core.events import build_context_note
from openai import OpenAI

client = OpenAI()


def respond(text: str, mode: str, state):
    system = MODES.get(mode, MODES["Normalny"])
    context = build_context_note(state)

    messages = [
        {"role": "system", "content": system + "\n" + context}
    ]

    for _, u, b in recent():
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": b})

    messages.append({"role": "user", "content": text})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )

    return resp.choices[0].message.content.strip()
