import inspect
from typing import Callable, TypeVar, Coroutine, Any

from discord.utils import MISSING
from discord.app_commands.commands import _shorten as shorten

from templates.commands import Command

T = TypeVar('T')
Coro = Coroutine[Any, Any, T]
CommandCallback = Callable[..., Coro[T]]


def command(
        *,
        name: str = MISSING,
        description: str = MISSING,
        help: str = MISSING,
        icon: str = MISSING
) -> Callable[[CommandCallback], Command]:
    """Creates an application command from a regular function.

    Parameters
    ------------
    name: :class:`str`
        The name of the application command. If not given, it defaults to a lower-case
        version of the callback name.
    description: :class:`str`
        The description of the application command. This shows up in the UI to describe
        the application command. If not given, it defaults to the first line of the docstring
        of the callback shortened to 100 characters.
    help: :class:`str`
        Extra information to include in the description when information is requested in a
        help command.
    icon: :class:`str`
        An emoji to include in certain views showing information about the command.
    """

    def decorator(func: CommandCallback) -> Command:
        if not inspect.iscoroutinefunction(func):
            raise TypeError('command function must be a coroutine function')

        if description is MISSING:
            if func.__doc__ is None:
                desc = '…'
            else:
                desc = shorten(func.__doc__)
        else:
            desc = description

        return Command(
            name=name if name is not MISSING else func.__name__,
            description=desc,
            callback=func,
            parent=None,
            help=help,
            icon=icon
        )

    return decorator
