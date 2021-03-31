from typing import Generator, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .paradigms import Call


Calls = Generator['Call', Any, None]
