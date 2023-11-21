from dataclasses import dataclass
from optparse import Option
from typing import Optional


@dataclass
class AccountDTO:

    username: Optional[str]
    firstname: Optional[str]
    lastname: Optional[str]
    middlename: Optional[str]
    password: Optional[str]
    role: Optional[str]
