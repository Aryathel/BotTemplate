import datetime

import pytimeparse


def tdelta_from_str(inp: str) -> datetime.timedelta:
    seconds = pytimeparse.parse(inp)
    return datetime.timedelta(seconds=seconds)


def get_emoji_name(emoji: str) -> str:
    return emoji.encode('ascii', 'namereplace').decode('utf-8')
