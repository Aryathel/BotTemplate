from datetime import timedelta
from typing import Union


import pytimeparse


def clamp(num: Union[int, float], min_val: Union[int, float] = None, max_val: Union[int, float] = None) -> Union[int, float]:
    if max_val and min_val:
        return min(max(num, min_val), max_val)
    elif max_val:
        return min(num, max_val)
    elif min_val:
        return max(num, min_val)


def get_emoji_name(emoji: str) -> str:
    return emoji.encode('ascii', 'namereplace').decode('utf-8')


def tdelta_from_str(inp: str) -> timedelta:
    seconds = pytimeparse.parse(inp)
    return timedelta(seconds=seconds)


def str_from_tdelta(duration: timedelta) -> str:
    str_form = str(duration).split(' ')
    if len(str_form) > 2:
        res = ' '.join(str_form[:2])
    else:
        res = ''

    hours, minutes, seconds = str_form[-1].split(':')
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)
    if hours > 0:
        res += f'{" " if not res == "" else ""}{hours} Hours'
    if minutes > 0:
        res += f'{", " if not res == "" else ""}{minutes} Minutes'
    if seconds > 0:
        res += f'{", " if not res == "" else ""}{seconds} Seconds'

    return res
