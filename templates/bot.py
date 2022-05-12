import asyncio
import traceback
from typing import Optional, Any, Type, Union, List, Dict, Mapping, TypeVar, Generator

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
from pyshorteners import Shortener

import database
from utils import LogType, EmbedFactory, log
from utils import TermColor as color
from .commands import Command, Group

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
    slash_commands: List[str]
    help: str = None

    def __init__(self, bot: BotType):
        self.bot = bot

    def cog_load(self) -> None:
        self.bot.log(f'{self.qualified_name} loaded...')

    def cog_unload(self) -> None:
        self.bot.log(f'{self.qualified_name} unloaded...')

    @property
    def long_description(self) -> str:
        if self.help is not None:
            if self.description not in ['...', None, MISSING]:
                return f'{self.description}\n\n{self.help}'
            return self.help
        else:
            return self.description


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
            await interaction.response.send_message(
                "Sorry, this command is unavailable. It likely has received an update in the backend, "
                "and needs to be re-synced.", ephemeral=True
            )
            self.client.log(
                f'Commands need to be synced. Source: "{interaction.command.name}"',
                urgent=True,
                log_type=LogType.warning
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            perms = []
            for p in error.missing_permissions:
                perms.append(f"`{' '.join(w.capitalize() for w in p.split('_'))}`")
            await interaction.response.send_message(
                f'Please give me the following permissions to use this command: {", ".join(perms)}',
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            perms = []
            for p in error.missing_permissions:
                perms.append(f"`{' '.join(w.capitalize() for w in p.split('_'))}`")
            await interaction.response.send_message(
                f'You are missing the following permissions to use this command: {", ".join(perms)}',
                ephemeral=True
            )
        elif isinstance(error, app_commands.TransformerError):
            await interaction.response.send_message(
                f'Failed to convert `{error.value}` to a `{error.type.name}`.',
                ephemeral=True
            )
        elif isinstance(error, discord.Forbidden):
            await interaction.response.send_message(
                f'I do not have permission to do that.',
                ephemeral=True
            )
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
            "cogs.moderation"
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
            urgent: Optional[bool] = None, error: Optional[BaseException] = None, rel: int = 2) -> None:
        msg = ' '.join(str(arg) for arg in args)
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

        if divider:
            log(f'-------- {msg} --------', rel=rel)
        else:
            log(f' > {msg}', rel=rel)

        if error is not None:
            print()
            for line in traceback.TracebackException(type(error), error, error.__traceback__).format():
                print(f'{"":>26} > {line}', end='')
            if divider:
                print(f'{"":>26}----------------', end='')

        color.reset()

    @classmethod
    def debug(cls, *args) -> None:
        cls.log('DEBUG:', *args, log_type=LogType.debug, rel=3)

    @property
    def cog_names(self) -> List[str]:
        cogs = [(name, cog) for name, cog in self.cogs.items() if not cog.qualified_name == 'admin']
        cogs = sorted(cogs, key=lambda e: e[0])
        return [c[0] for c in cogs]

    def get_command_autocomplete_list(self) -> Dict[str, Union[Cog, Command, Group]]:
        choices: Dict[str, Union[Cog, Command, Group]] = {}
        for _, cog in self.cogs.items():
            if not cog.qualified_name == 'admin':
                choices[cog.name] = cog

        for command in self.tree.walk_commands(guild=self.GUILD):
            choices[command.qualified_name.lower()] = command

        return choices
