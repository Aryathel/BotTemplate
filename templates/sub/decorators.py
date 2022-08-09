from enum import Enum
import inspect
from typing import Callable, TypeVar, Coroutine, Any, Type
from functools import wraps

from discord.utils import MISSING
from discord import app_commands
from discord.app_commands.commands import _shorten as shorten, _populate_choices as populate_choices

from templates.commands import Command

T = TypeVar('T')
Coro = Coroutine[Any, Any, T]
CommandCallback = Callable[..., Coro[T]]


def _error_catcher(handlers):
    def inner(func):
        @wraps(func)
        async def decorator(self, *args, **kwargs):
            try:
                await func(self, *args, **kwargs)
            except Exception as err:
                for handler in handlers:
                    await handler(self, err, *args, **kwargs)

        return decorator

    return inner


def catch_errors(cls):
    _error_handlers = []
    for name, method in cls.__dict__.items():
        if hasattr(method, '_error_handler'):
            _error_handlers.append(method)

    if not _error_handlers:
        raise Exception("A class decorated by \"catch_errors\" must have at least one method decorated by \"error_handler\"")

    for name, method in cls.__dict__.items():
        if hasattr(method, '_handle_errors'):
            if hasattr(cls, method.__name__):
                setattr(cls, method.__name__, _error_catcher(_error_handlers)(method))

    return cls


def handle_errors(func):
    func._handle_errors = True
    return func


def error_handler(func):
    func._error_handler = True
    return func


def command(
        *,
        name: str = MISSING,
        description: str = MISSING,
        nsfw: bool = False,
        help: str = MISSING,
        icon: str = MISSING,
        parent=None,
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
    nsfw: :class:`bool`
        Whether the command should be flagged as NSFW on Discord's end.
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
            nsfw=nsfw,
            callback=func,
            parent=parent,
            help=help,
            icon=icon
        )

    return decorator


def enum_choices(**parameters: Type[Enum]) -> Callable[[T], T]:
    actual: dict[str, list[app_commands.Choice]] = {}
    for param, enum in parameters.items():
        if not issubclass(enum, Enum):
            raise ValueError(f"The {param} argument must be an Enum.")

        tmp = []
        for name, value in enum.__members__.items():
            value = value.value
            if isinstance(value, str):
                tmp.append(app_commands.Choice(name=value, value=value))
            else:
                tmp.append(app_commands.Choice(name=' '.join(w.lower().capitalize() for w in name.split('_')), value=value))
        if tmp:
            actual[param] = tmp

    def decorator(inner: T) -> T:
        if isinstance(inner, Command):
            populate_choices(inner._params, actual)
        else:
            try:
                inner.__discord_app_commands_param_choices__.update(actual)  # type: ignore # Runtime attribute access
            except AttributeError:
                inner.__discord_app_commands_param_choices__ = actual  # type: ignore # Runtime attribute assignment

        return inner

    return decorator