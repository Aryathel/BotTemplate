import discord
from discord import app_commands

from templates import Cog, Bot


class SettingsCog(Cog, name='settings'):
    slash_commands = []


async def setup(bot: Bot) -> None:
    await bot.add_cog(SettingsCog(bot), guilds=[bot.GUILD])
