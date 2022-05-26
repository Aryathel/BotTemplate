from typing import Mapping, Union

from discord import app_commands

from templates import Interaction, Cog, Command, Group, Bot
from templates import decorators, checks, helpmenu, transformers
from utils import LogType, Menu


class AdminCog(Cog, name='admin'):
    slash_commands = ['help', 'sync']

    @decorators.command(
        name='help',
        description='Returns usage info about available commands.',
        icon='\N{EXCLAMATION QUESTION MARK}'
    )
    @app_commands.describe(command='A command, or group of commands, to get information for.')
    async def help_command(
            self,
            interaction: Interaction,
            command: app_commands.Transform[Union[Cog, Group, Command], transformers.CommandTransformer] = None
    ):
        if command is None:
            bot_cogs: Mapping[str, Cog] = self.bot.cogs
            cogs = [(name, cog) for name, cog in bot_cogs.items() if not cog.qualified_name == 'admin']
            cogs = sorted(cogs, key=lambda e: e[0])

            mapping = {}
            for name, cog in cogs:
                mapping[cog] = [self.bot.tree.get_command(c, guild=self.bot.GUILD) for c in cog.slash_commands]

            menu = helpmenu.HelpMenu(helpmenu.HelpMenuIndex(self.bot.embeds), interaction)
            menu.add_modules(mapping)
            await menu.start()
        else:
            if isinstance(command, app_commands.Command):
                menu = Menu(helpmenu.HelpMenuCommand(command, self.bot.embeds), interaction)
                await menu.start()

            elif isinstance(command, Group):
                menu = Menu(
                    helpmenu.HelpMenuGroup(
                        group=command,
                        commands_per_page=5,
                        embed_factory=self.bot.embeds,
                        in_bulk_help=False
                    ),
                    interaction
                )
                await menu.start()

            elif isinstance(command, Cog):
                cog: Cog = command
                comms = [self.bot.tree.get_command(c, guild=self.bot.GUILD) for c in cog.slash_commands]
                menu = Menu(
                    helpmenu.HelpMenuCog(
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
    @checks.is_owner()
    async def sync_commands(self, interaction: Interaction) -> None:
        await interaction.response.send_message(
            embed=self.bot.embeds.get(description='Syncing commands.'),
            ephemeral=True
        )
        await self.bot.tree.sync(guild=self.bot.GUILD)
        self.bot.log('Synced commands to Discord.', log_type=LogType.warning)

    @sync_commands.error
    async def sync_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original
        if isinstance(error, app_commands.CheckFailure):
            emb = self.bot.embeds.get(
                description='You need to be my creator to do that, and you are not. Sorry ¯\\_(ツ)_/¯'
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            interaction.extras['handled'] = True


async def setup(bot: Bot) -> None:
    await bot.add_cog(AdminCog(bot), guilds=[bot.GUILD])
