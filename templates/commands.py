import inspect
from typing import Callable, TypeVar, Coroutine, Any, Union, Optional, MutableMapping, List

from discord import app_commands
from discord.app_commands.commands import _shorten as shorten
from discord.utils import MISSING

P = TypeVar('P')
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
GroupT = TypeVar('GroupT', bound='Binding')
Coro = Coroutine[Any, Any, T]
Binding = Union['Group', 'Cog']
CommandCallback = Callable[..., Coro[T]]
CommandType = TypeVar('CommandType', bound='Command')
GroupType = TypeVar('GroupType', bound='Group')
Check = Callable[['Interaction'], Union[bool, Coro[bool]]]


class Group(app_commands.Group):
    icon: str = None
    help: str = None
    desc: str = None
    commands: List[Union[CommandType, GroupType]]

    def __init__(
            self,
            bot = None,
            help: str = None,
            icon: str = None,
            description: str = None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs, description=description)

        self.help = help
        self.icon = icon
        self.desc = description
        self.description = f'{self.icon} {description}' if self.icon else self.description
        self.bot = bot

    @property
    def long_description(self) -> str:
        if self.help is not None:
            if self.desc not in ['...', None, MISSING]:
                return f'{self.desc}\n\n{self.help}'
            return self.help
        else:
            return self.desc

    def _copy_with(
            self,
            *,
            parent: Optional[GroupType],
            binding: Binding,
            bindings: MutableMapping[GroupType, GroupType] = MISSING,
            set_on_binding: bool = True,
    ) -> GroupType:
        bindings = {} if bindings is MISSING else bindings

        cls = self.__class__
        copy = cls.__new__(cls)
        copy.name = self.name
        copy._guild_ids = self._guild_ids
        copy.description = self.description
        copy.parent = parent
        copy.module = self.module
        copy.default_permissions = self.default_permissions
        copy.guild_only = self.guild_only
        copy.nsfw = self.nsfw
        copy._attr = self._attr
        copy._owner_cls = self._owner_cls
        copy._children = {}
        copy.bot = self.bot

        copy.icon = self.icon
        copy.help = self.help
        copy.desc = self.desc

        bindings[self] = copy

        for child in self._children.values():
            child_copy = child._copy_with(parent=copy, binding=binding, bindings=bindings)
            child_copy.parent = copy
            copy._children[child_copy.name] = child_copy

            if isinstance(child_copy, app_commands.Group) and child_copy._attr and set_on_binding:
                if binding.__class__ is child_copy._owner_cls:
                    setattr(binding, child_copy._attr, child_copy)
                elif child_copy._owner_cls is copy.__class__:
                    setattr(copy, child_copy._attr, child_copy)

        if copy._attr and set_on_binding:
            setattr(parent or binding, copy._attr, copy)

        return copy

    def command(
            self,
            *,
            name: str = MISSING,
            description: str = MISSING,
            help: str = MISSING,
            icon: str = MISSING
    ) -> Callable[[CommandCallback], app_commands.Command]:
        """Creates an application command under this group.

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

        def decorator(func: CommandCallback) -> app_commands.Command:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('command function must be a coroutine function')

            if description is MISSING:
                if func.__doc__ is None:
                    desc = '…'
                else:
                    desc = shorten(func.__doc__)
            else:
                desc = description

            command = Command(
                name=name if name is not MISSING else func.__name__,
                description=desc,
                callback=func,
                parent=self,
                icon=icon,
                help=help
            )
            self.add_command(command)
            return command

        return decorator


class Command(app_commands.Command):
    icon: str = None
    help: str = None
    desc: str = None
    checks: List[Check]

    def __init__(
            self,
            help: str = None,
            icon: str = None,
            description: str = None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs, description=description)

        self.help = help
        self.icon = icon
        self.desc = description
        self.description = f'{self.icon} {description}' if self.icon else self.description

    @property
    def long_description(self) -> str:
        if self.help is not None:
            if self.desc not in ['...', None, MISSING]:
                return f'{self.desc}\n\n{self.help}'
            return self.help
        else:
            return self.desc

    def _copy_with(
            self,
            *,
            parent: Optional[Group],
            binding: GroupT,
            bindings: MutableMapping[GroupT, GroupT] = MISSING,
            set_on_binding: bool = True,
    ) -> CommandType:
        bindings = {} if bindings is MISSING else bindings

        cls = self.__class__
        copy = cls.__new__(cls)
        copy.name = self.name
        copy._guild_ids = self._guild_ids
        copy.checks = self.checks
        copy.description = self.description
        copy.default_permissions = self.default_permissions
        copy.guild_only = self.guild_only
        copy.nsfw = self.nsfw
        copy._attr = self._attr
        copy._callback = self._callback
        copy.on_error = self.on_error
        copy._params = self._params.copy()
        copy.module = self.module
        copy.parent = parent
        copy.binding = bindings.get(self.binding) if self.binding is not None else binding

        copy.icon = self.icon
        copy.help = self.help
        copy.desc = self.desc

        if copy._attr and set_on_binding:
            setattr(copy.binding, copy._attr, copy)

        return copy
