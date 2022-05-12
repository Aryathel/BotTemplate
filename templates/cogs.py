from typing import List, TypeVar
from discord.ext import commands
from discord.utils import MISSING

from .bot import AryaBot


class AryaCog(commands.Cog):
    bot: AryaBot
    name: str
    description: str
    icon: str
    slash_commands: List[str]
    help: str = None

    def __init__(self, bot: AryaBot):
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
