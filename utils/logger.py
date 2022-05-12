import inspect
from enum import Enum
import os


class LogType(Enum):
    """The possible types for a log sent through the bot.

    These types are then used to control the color of the log as it is printed to the terminal.
    """
    normal = 1
    ok = 2
    warning = 3
    error = 4
    debug = 5


def log(msg: str = "", /, rel: int = 2, end: str = ''):
    frame = inspect.stack()[rel][0]

    func = frame.f_code.co_name
    filename = frame.f_code.co_filename.replace(os.path.abspath('.') + '\\', '')
    line_no = frame.f_lineno

    print(f'{filename:>20}:{line_no:<4} {msg}', end=end)
