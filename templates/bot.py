import asyncio
import traceback
from typing import Optional, Any, Type, Union, List, Dict, Mapping, TypeVar, Generator, ClassVar, TYPE_CHECKING

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
from pyshorteners import Shortener

import database
from database.models.twitter_monitors import TwitterMonitor
from utils import LogType, EmbedFactory, log, command_name, TermColor as color
from .commands import Command, Group
from .errors import TransformerError

if TYPE_CHECKING:
    from tweepy.asynchronous import AsyncClient

BotType = TypeVar('BotType', bound='Bot')


class Intents(discord.Intents):
    def update(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class Interaction(discord.Interaction):
    client: BotType


class Cog(commands.Cog):
    bot: BotType
    name: str
    description: str
    icon: str
    slash_commands: List[Union[str, Group, 'GroupCog']]
    help: str = None
    nested: bool = False

    ignore_load_unload: bool = False

    def __new__(cls, *args: Any, **kwargs: Any):
        # For issue 426, we need to store a copy of the command objects
        # since we modify them to inject `self` to them.
        # To do this, we need to interfere with the Cog creation process.
        self = super().__new__(cls)
        cmd_attrs = cls.__cog_settings__

        # Either update the command with the cog provided defaults or copy it.
        # r.e type ignore, type-checker complains about overriding a ClassVar
        self.__cog_commands__ = tuple(c._update_copy(cmd_attrs) for c in cls.__cog_commands__)  # type: ignore

        lookup = {cmd.qualified_name: cmd for cmd in self.__cog_commands__}

        # Register the application commands
        children: List[Union[app_commands.Group, app_commands.Command[..., ..., Any]]] = []

        if cls.__cog_is_app_commands_group__:
            group = Group(
                help=cls.help,
                name=cls.__cog_group_name__,
                description=cls.description,
                nsfw=cls.__cog_group_nsfw__,
                parent=None,
                guild_ids=getattr(cls, '__discord_app_commands_default_guilds__', None),
                guild_only=getattr(cls, '__discord_app_commands_guild_only__', False),
                default_permissions=getattr(cls, '__discord_app_commands_default_permissions__', None),
            )
        else:
            group = None

        self.__cog_app_commands_group__ = group

        # Update the Command instances dynamically as well
        for command in self.__cog_commands__:
            setattr(self, command.callback.__name__, command)
            parent = command.parent
            if parent is not None:
                # Get the latest parent reference
                parent = lookup[parent.qualified_name]  # type: ignore

                # Update our parent's reference to our self
                parent.remove_command(command.name)  # type: ignore
                parent.add_command(command)  # type: ignore

            if hasattr(command, '__commands_is_hybrid__') and parent is None:
                app_command: Optional[Union[app_commands.Group, app_commands.Command[Self, ..., Any]]] = getattr(
                    command, 'app_command', None
                )
                if app_command:
                    group_parent = self.__cog_app_commands_group__
                    app_command = app_command._copy_with(parent=group_parent, binding=self)
                    # The type checker does not see the app_command attribute even though it exists
                    command.app_command = app_command  # type: ignore

                    if self.__cog_app_commands_group__:
                        children.append(app_command)

        for command in cls.__cog_app_commands__:
            copy = command._copy_with(parent=self.__cog_app_commands_group__, binding=self)

            # Update set bindings
            if copy._attr:
                setattr(self, copy._attr, copy)

            children.append(copy)

        self.__cog_app_commands__ = children
        if self.__cog_app_commands_group__:
            self.__cog_app_commands_group__.module = cls.__module__
            mapping = {cmd.name: cmd for cmd in children}
            if len(mapping) > 25:
                raise TypeError('maximum number of application command children exceeded')

            self.__cog_app_commands_group__._children = mapping  # type: ignore  # Variance issue

        return self

    def __init__(self, bot: BotType):
        self.bot = bot

    def cog_load(self) -> None:
        if self.nested:
            return

        self.bot.log(f'{self.qualified_name} loading...', nest=1)
        for c in sorted(self.slash_commands, key=command_name):
            if isinstance(c, Group) or isinstance(c, GroupCog):
                group_name = command_name(c)
                self.bot.log(f'{group_name} loading...', nest=2)
                if isinstance(c, Group):
                    obj = c
                else:
                    obj = c.app_command
                for sub_c in obj.walk_commands():
                    name = command_name(sub_c)
                    if isinstance(sub_c, Group) or isinstance(sub_c, GroupCog):
                        self.bot.log(f'{name} loading...', nest=3)
                        if isinstance(sub_c, Group):
                            sub_obj = c
                        else:
                            sub_obj = sub_c.app_command
                        for sub_sub_c in sub_obj.walk_commands():
                            name = command_name(sub_sub_c)
                            self.bot.log(f'{name} added.', nest=4)
                    else:
                        self.bot.log(f'{name} added.', nest=3)
                self.bot.log(f'{group_name} loaded.', nest=2)
            else:
                self.bot.log(f'{c} added', nest=2)
        self.bot.log(f'{self.qualified_name} loaded.', nest=1)

    def cog_unload(self) -> None:
        if self.nested:
            return

        self.bot.log(f'{self.qualified_name} unloading...', nest=1)
        for c in sorted(self.slash_commands, key=command_name):
            if isinstance(c, Group) or isinstance(c, GroupCog):
                name = command_name(c)
                self.bot.log(f'{name} unloading...', nest=2)
                if isinstance(c, Group):
                    obj = c
                else:
                    obj = c.app_command
                for sub_c in obj.walk_commands():
                    name = command_name(sub_c)
                    if isinstance(sub_c, Group) or isinstance(sub_c, GroupCog):
                        self.bot.log(f'{name} unloading...', nest=3)
                        if isinstance(sub_c, Group):
                            sub_obj = c
                        else:
                            sub_obj = sub_c.app_command
                        for sub_sub_c in sub_obj.walk_commands():
                            name = command_name(sub_sub_c)
                            self.bot.log(f'{name} removed.', nest=4)
                    else:
                        self.bot.log(f'{sub_c.name} removed.', nest=3)
            else:
                self.bot.log(f'{c} removed', nest=2)
        self.bot.log(f'{self.qualified_name} unloaded.', nest=1)

    @property
    def long_description(self) -> str:
        if self.help is not None:
            if self.description not in ['...', None, MISSING]:
                return f'{self.description}\n\n{self.help}'
            return self.help
        else:
            return self.description

    def __repr__(self) -> str:
        return f'<cogs.{self.__class__.__name__}>'


class GroupCog(Cog):
    __cog_is_app_commands_group__: ClassVar[bool] = True


class CommandTree(app_commands.CommandTree):
    client: BotType
    _guild_commands: Dict[int, Dict[str, Union[Command, Group]]]
    _global_commands: Dict[str, Union[Command, Group]]

    async def on_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if interaction.extras.get('handled', False):
            return

        needs_syncing = (
            app_commands.CommandSignatureMismatch,
            app_commands.CommandNotFound
        )

        if isinstance(error, needs_syncing):
            emb = self.client.embeds.get(
                description="Sorry, this command is unavailable. It likely has received an update in the backend, "
                            "and needs to be re-synced.",
                color=discord.Color.brand_red()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            self.client.log(
                f'Commands need to be synced. Source: "{interaction.command.name}"',
                urgent=True,
                log_type=LogType.warning
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            perms = []
            for p in error.missing_permissions:
                perms.append(f"`{' '.join(w.capitalize() for w in p.split('_'))}`")
            emb = self.client.embeds.get(
                description=f'Please give me the following permissions to use this command: {", ".join(perms)}',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
        elif isinstance(error, app_commands.MissingPermissions):
            perms = []
            for p in error.missing_permissions:
                perms.append(f"`{' '.join(w.capitalize() for w in p.split('_'))}`")
            emb = self.client.embeds.get(
                description=f'You are missing the following permissions to use this command: {", ".join(perms)}',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
        elif isinstance(error, TransformerError):
            emb = self.client.embeds.get(
                description=f'Failed to convert `{error.value}` to a `{error.type.name}`.',
                color=discord.Color.brand_red()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
        elif isinstance(error, discord.Forbidden):
            emb = self.client.embeds.get(
                description=f'I do not have permission to do that.',
                color=discord.Color.brand_red()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
        else:
            self.client.log(
                f'Unhandled "{type(error).__name__}" in "{interaction.command.name}" Command',
                log_type=LogType.error,
                error=error,
                divider=True
            )

        interaction.extras['handled'] = True

    def walk_commands(
            self,
            *,
            guild: Optional[discord.abc.Snowflake] = None,
            type: discord.AppCommandType = discord.AppCommandType.chat_input,
    ) -> Union[Generator[Union[Command, Group], None, None], Generator[app_commands.ContextMenu, None, None]]:
        if type is discord.AppCommandType.chat_input:
            if guild is None:
                for cmd in self._global_commands.values():
                    yield cmd
                    if isinstance(cmd, Group):
                        yield from cmd.walk_commands()
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return
                else:
                    for cmd in commands.values():
                        yield cmd
                        if isinstance(cmd, Group):
                            yield from cmd.walk_commands()
        else:
            guild_id = None if guild is None else guild.id
            value = type.value
            for ((_, g, t), command) in self._context_menus.items():
                if g == guild_id and t == value:
                    yield command


class Bot(commands.Bot):
    db: Optional[database.Client]
    command_autocomplete_list: Dict[str, Union[Cog, Command, Group]]
    cogs: Mapping[str, Cog]
    tree: CommandTree

    twitter: Optional['AsyncClient']
    twitter_monitors: Optional[list[TwitterMonitor]]

    def __init__(
            self,
            command_prefix: str,
            description: str,
            token: str,
            guild: discord.Object,
            owner_id: int,
            db_name: str,
            db_host: str,
            db_port: Union[str, int],
            db_user: str,
            db_pass: str,
            tree_cls: Type[app_commands.CommandTree] = CommandTree,
            embed_factory: EmbedFactory = EmbedFactory()
    ) -> None:
        intents = Intents.default()
        intents.update(
            members=True,
            presences=True,
            reactions=True
        )

        # Register internal constants
        self.COGS = [
            "cogs.admin",
            "cogs.misc",
            "cogs.moderation",
            "cogs.twitter",
        ]
        self.TOKEN = token
        self.GUILD = guild
        self.OWNER_ID = owner_id

        self._db_name = db_name
        self._db_host = db_host
        self._db_port = db_port
        self._db_user = db_user
        self._db_pass = db_pass

        # Register embed factory.
        self.embeds = embed_factory

        # Register URL shortener
        self.url_shorter = Shortener()

        super().__init__(
            command_prefix=command_prefix,
            description=description,
            intents=intents,
            tree_cls=tree_cls
        )

    async def setup_hook(self) -> None:
        # Register PostgreSQL database connection pool.
        self.log('Connecting to PostgreSQL database...')
        pool = await asyncpg.create_pool(
            host=self._db_host,
            port=self._db_port,
            database=self._db_name,
            user=self._db_user,
            password=self._db_pass
        )
        self.db = database.Client(pool)
        self.log('Initializing database...')
        await self.db.initialize()
        self.log('Database connected and loaded.', log_type=LogType.ok, divider=True)

        # Register Cog extensions.
        self.log('Loading cogs...')
        for cog in self.COGS:
            await self.load_extension(cog)
        self.log('Cogs loaded.', log_type=LogType.ok, divider=True)

        # Register persistent views here. None are currently used.
        pass

        # Generate embeds for the help command.
        self.command_autocomplete_list = self.get_command_autocomplete_list()

    async def on_ready(self):
        self.log(
            f'Bot logged in as {self.user} (ID: {self.user.id})',
            divider=True,
            log_type=LogType.ok,
            urgent=True
        )

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        self.log(f'Ignoring exception in {event_method}', log_type=LogType.error)
        traceback.print_exc()

    async def on_command_error(self, ctx: commands.Context, exception: commands.CommandError, /) -> None:
        command = ctx.command
        if command and command.has_error_handler():
            return

        cog = ctx.cog
        if cog and cog.has_error_handler():
            return

        self.log(f'Ignoring exception in command {ctx.command}:', log_type=LogType.error, error=exception)

    def run(self, *args: Any, **kwargs: Any) -> None:
        kwargs['token'] = self.TOKEN

        async def runner():
            async with self:
                await self.start(*args, **kwargs)

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            return

    @staticmethod
    def log(*args, log_type: LogType = LogType.normal, divider: bool = False,
            urgent: Optional[bool] = None, error: Optional[BaseException] = None,
            rel: int = 2, separator: str = ' ', nest: int = 0) -> None:
        separator = separator if type(separator) == str else ' '
        nest_space = "\t" * nest
        msg = separator.join(str(arg) for arg in args)
        if urgent:
            color.black(bg=True)

        if log_type == LogType.ok:
            if urgent:
                color.green(bg=True)
            else:
                color.green()
        elif log_type == LogType.warning:
            if urgent:
                color.yellow(bg=True)
            else:
                color.yellow()
        elif log_type == LogType.error:
            if urgent:
                color.red(bg=True)
            else:
                color.red()
        elif log_type == LogType.debug:
            if urgent:
                color.magenta(bg=True)
            else:
                color.magenta()
        elif log_type == LogType.twitter:
            if urgent:
                color.blue(bg=True)
                color.black()
            else:
                color.blue()

        if divider:
            log(f'{nest_space}-------- {msg} --------', rel=rel)
        else:
            log(f'{nest_space} > {msg}', rel=rel)

        if error is not None:
            print()
            for line in traceback.TracebackException(type(error), error, error.__traceback__).format():
                print(f'{nest_space}{"":>26} > {line}', end='')
            if divider:
                print(f'{nest_space}{"":>26}----------------', end='')

        color.reset()

    @classmethod
    def debug(cls, *args, **kwargs) -> None:
        cls.log('DEBUG:', *args, **kwargs, log_type=LogType.debug, rel=3)

    @property
    def cog_names(self) -> List[str]:
        cogs = [(name, cog) for name, cog in self.cogs.items() if not cog.qualified_name == 'admin']
        cogs = sorted(cogs, key=lambda e: e[0])
        return [c[0] for c in cogs]

    def get_command_autocomplete_list(self) -> Dict[str, Union[Cog, Command, Group]]:
        choices: Dict[str, Union[Cog, Command, Group]] = {}
        for _, cog in self.cogs.items():
            if not cog.qualified_name == 'admin':
                if isinstance(cog, GroupCog):
                    choices[cog.__cog_group_name__] = cog
                else:
                    choices[cog.name] = cog

        for command in self.tree.walk_commands(guild=self.GUILD):
            choices[command.qualified_name.lower()] = command

        return choices
