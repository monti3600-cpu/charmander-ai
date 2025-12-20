from dataclasses import dataclass
from datetime import datetime


@dataclass
class State:
    listening: bool = False
    paused: bool = False
    last_interaction: datetime | None = None
