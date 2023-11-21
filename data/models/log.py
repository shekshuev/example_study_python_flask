from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass
class Log:

    id: int
    date: date
    time: time
    type: str
    user_id: Optional[int]
    event: str
    reason: str
