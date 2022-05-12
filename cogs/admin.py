from typing import Mapping, Union

import discord
from discord import app_commands
from discord.ext import commands

from custom_types import CommandOrGroupOrCog, CommandTransformer
from templates import AryaBot, AryaCog, AryaInteraction, is_arya, HelpMenu, HelpMenuIndex, debug, Menu, HelpMenuCommand, \
    HelpMenuCog, aryacommand, HelpMenuGroup
from utils import LogType


class AdminCog(AryaCog, name='admin'):
    @aryacommand(
        name='help',
        description='Returns usage info about available commands.',
        icon='\N{EXCLAMATION QUESTION MARK}'
    )
    @app_commands.describe(command='A command, or group of commands, to get information for.')
    async def help_command(self, interaction: AryaInteraction,
                           command: app_commands.Transform[CommandOrGroupOrCog, CommandTransformer] = None):
        if command is None:
            bot_cogs: Mapping[str, AryaCog] = self.bot.cogs
            cogs = [(name, cog) for name, cog in bot_cogs.items() if not cog.qualified_name == 'admin']
            cogs = sorted(cogs, key=lambda e: e[0])

            mapping = {}
            for name, cog in cogs:
                mapping[cog] = [self.bot.tree.get_command(c, guild=self.bot.GUILD) for c in cog.slash_commands]

            menu = HelpMenu(HelpMenuIndex(self.bot.embeds), interaction)
            menu.add_modules(mapping)
            await menu.start()
        else:
            obj: Union[app_commands.Command, app_commands.Group, AryaCog] = command.object
            if isinstance(obj, app_commands.Command):
                menu = Menu(HelpMenuCommand(obj, self.bot.embeds), interaction)
                await menu.start()

            elif isinstance(obj, app_commands.Group):
                menu = Menu(
                    HelpMenuGroup(
                        group=obj,
                        commands_per_page=5,
                        embed_factory=self.bot.embeds,
                        in_bulk_help=False
                    ),
                    interaction
                )
                await menu.start()

            elif isinstance(obj, commands.Cog):
                cog: AryaCog = obj
                comms = [self.bot.tree.get_command(c, guild=self.bot.GUILD) for c in cog.slash_commands]
                menu = Menu(
                    HelpMenuCog(
                        cog=cog,
                        commands=comms,
                        commands_per_page=5,
                        embed_factory=self.bot.embeds,
                        in_bulk_help=False
                    ),
                    interaction
                )
                await menu.start()

    @app_commands.command(name='sync',
                          description='\N{Envelope with Downwards Arrow Above} Syncs the slash commands to Discord.')
    @is_arya()
    async def sync_commands(self, interaction: AryaInteraction) -> None:
        await interaction.response.send_message('Commands syncing...', ephemeral=True)
        await self.bot.tree.sync(guild=self.bot.GUILD)
        self.bot.log('Synced commands to Discord.', log_type=LogType.warning)

    @sync_commands.error
    async def sync_error(self, interaction: AryaInteraction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                'You need to be my creator to do that, and you are not. Sorry ¯\\_(ツ)_/¯', ephemeral=True)
            interaction.extras['handled'] = True


async def setup(bot: AryaBot) -> None:
    await bot.add_cog(AdminCog(bot), guilds=[bot.GUILD])
