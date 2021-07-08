from collections import namedtuple

from .paradigm import Paradigm
from .paradigms import Paradigms


Call = namedtuple('Call', ('obj', 'args', 'kw'))

paradigms = Paradigms()

normal = paradigms.register_if_possible('mush.paradigms.normal_', 'Normal')
asyncio = paradigms.register_if_possible('mush.paradigms.asyncio_', 'AsyncIO')

paradigms.add_shifter_if_possible(normal, asyncio, 'mush.paradigms.asyncio_', 'asyncio_to_normal')
