from datetime import timedelta
from typing import Union


import pytimeparse


def clamp(num: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    return min(max(num, min_val), max_val)


def get_emoji_name(emoji: str) -> str:
    return emoji.encode('ascii', 'namereplace').decode('utf-8')


def tdelta_from_str(inp: str) -> timedelta:
    seconds = pytimeparse.parse(inp)
    return timedelta(seconds=seconds)
