from dataclasses import dataclass


@dataclass
class Account:

    id: int
    username: str
    firstname: str
    lastname: str
    middlename: str
    role: str
