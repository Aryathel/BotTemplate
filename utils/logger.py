import inspect
from enum import Enum
import os

from colorama import init, Fore, Back, Style
init()


class TermColor:
    # Foreground (text) terminal coloring.
    BLACK = Fore.BLACK
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    MAGENTA = Fore.MAGENTA
    RED = Fore.RED
    WHITE = Fore.WHITE
    YELLOW = Fore.YELLOW
    # Background terminal coloring.
    BLACK_BG = Back.BLACK
    BLUE_BG = Back.BLUE
    CYAN_BG = Back.CYAN
    GREEN_BG = Back.GREEN
    MAGENTA_BG = Back.MAGENTA
    RED_BG = Back.RED
    WHITE_BG = Back.WHITE
    YELLOW_BG = Back.YELLOW
    # Text Styling
    DIM = Style.DIM
    NORMAL = Style.NORMAL
    BRIGHT = Style.BRIGHT
    # Reset styling.
    RESET = Style.RESET_ALL

    @classmethod
    def black(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.BLACK_BG, end=end)
        else:
            print(cls.BLACK, end=end)

    @classmethod
    def blue(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.BLUE_BG, end=end)
        else:
            print(cls.BLUE, end=end)

    @classmethod
    def cyan(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.CYAN_BG, end=end)
        else:
            print(cls.CYAN, end=end)

    @classmethod
    def green(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.GREEN_BG, end=end)
        else:
            print(cls.GREEN, end=end)

    @classmethod
    def magenta(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.MAGENTA_BG, end=end)
        else:
            print(cls.MAGENTA, end=end)

    @classmethod
    def red(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.RED_BG, end=end)
        else:
            print(cls.RED, end=end)

    @classmethod
    def white(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.WHITE_BG, end=end)
        else:
            print(cls.WHITE, end=end)

    @classmethod
    def yellow(cls, bg: bool = False, end: str = '') -> None:
        if bg:
            print(cls.YELLOW_BG, end=end)
        else:
            print(cls.YELLOW, end=end)

    @classmethod
    def dim(cls, end: str = '') -> None:
        print(cls.DIM, end=end)

    @classmethod
    def normal(cls, end: str = '') -> None:
        print(cls.NORMAL, end=end)

    @classmethod
    def bright(cls, end: str = '') -> None:
        print(cls.BRIGHT, end=end)

    @classmethod
    def reset(cls, end: str = '\n') -> None:
        print(cls.RESET, end=end)


class LogType(Enum):
    """The possible types for a log sent through the bot.

    These types are then used to control the color of the log as it is printed to the terminal.
    """
    normal = 'normal'
    ok = 'ok'
    warning = 'warning'
    error = 'error'
    debug = 'debug'
    twitter = 'twitter'


def log(msg: str = "", /, rel: int = 2, end: str = ''):
    frame = inspect.stack()[rel][0]

    filename = frame.f_code.co_filename.replace(os.path.abspath('.') + '\\', '')
    line_no = frame.f_lineno

    print(f'{filename:>20}:{line_no:<4} {msg}', end=end)
