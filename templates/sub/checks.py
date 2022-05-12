from typing import Union, Coroutine, Callable, TypeVar, Any

from discord import app_commands

from ..bot import Interaction
from ..commands import Command

T = TypeVar('T')
Coro = Coroutine[Any, Any, T]
Check = Callable[['AryaInteraction'], Union[bool, Coro[bool]]]
CommandCallback = Callable[..., Coro[T]]
ContextMenuCallback = Callable[..., Coro[T]]
CheckInputParameter = Union['AryaCommand[Any, ..., Any]', 'ContextMenu', CommandCallback, ContextMenuCallback]


def check(predicate: Check) -> Callable[[T], T]:
    def decorator(func: CheckInputParameter) -> CheckInputParameter:
        if isinstance(func, (Command, app_commands.ContextMenu)):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__discord_app_commands_checks__'):
                func.__discord_app_commands_checks__ = []

            func.__discord_app_commands_checks__.append(predicate)

        return func

    return decorator


def is_owner():
    def predicate(interaction: Interaction) -> bool:
        return interaction.user.id == interaction.client.OWNER_ID

    return check(predicate)
