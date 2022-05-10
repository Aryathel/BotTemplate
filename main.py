import os
import sys
import traceback
from typing import Optional

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from pyshorteners import Shortener

from utils.embeds import EmbedFactory
import database


class AryaCommandTree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
                "Sorry, this command seems to be unavailable! Please try again later...", ephemeral=True
            )
            await self.sync()
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
        else:
            print(f'Ignoring exception in application command {interaction.command!r}', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        interaction.extras['handled'] = True


class AryaBot(commands.Bot):
    db: Optional[database.Client] = None

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.reactions = True

        # Register internal constants
        self.COGS = [
            "cogs.general",
            "cogs.moderation"
        ]
        self.TOKEN = os.getenv('BOT_TOKEN')
        self.GUILD = discord.Object(id=int(os.getenv('BOT_GUILD')))
        self.OWNER_ID = int(os.getenv('BOT_OWNER'))

        # Register embed factory.
        self.embeds = EmbedFactory(
            color=discord.Colour.from_str(os.getenv('BOT_COLOR')),  # Purple:
            # footer='Arya\'s Template Bot | v2.0'
        )

        # Register URL shortener
        self.url_shorter = Shortener()

        super().__init__(
            command_prefix='!',
            description="This is Arya's template Discord.py v2.0 bot!",
            intents=intents,
            tree_cls=AryaCommandTree
        )

    async def setup_hook(self) -> None:
        # Register Cog extensions.
        for cog in self.COGS:
            await self.load_extension(cog)

        # Register PostgreSQL database connection pool.
        pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            database=os.getenv('POSTGRES_DB_NAME'),
            user=os.getenv('POSTGRES_DB_USER'),
            password=os.getenv('POSTGRES_DB_PASS')
        )
        self.db = database.Client(pool)
        await self.db.initialize()

        # Register persistent views here. None are currently used.
        pass

    async def on_ready(self):
        print(f'Bot logged in as {self.user} (ID: {self.user.id})')
        print('------')


if __name__ == "__main__":
    bot = AryaBot()
    bot.run(bot.TOKEN)
