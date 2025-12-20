from core.clock import is_night, long_pause


def build_context_note(state) -> str:
    notes = []

    if is_night():
        notes.append(
            "Jest noc. Odpowiadaj ciszej i narzekaj, że jesteś śpiący."
        )

    if long_pause(state.last_interaction):
        notes.append(
            "Minęła długa przerwa. Nie traktuj tego jako ciągłej rozmowy."
        )

    return " ".join(notes)
