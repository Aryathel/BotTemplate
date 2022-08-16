import discord
from discord import app_commands

from templates import GroupCog, decorators, Interaction
from utils import Menu, MenuPageList


@app_commands.guild_only()
class Warn(GroupCog, group_name='warnings', name='warnings'):
    description = 'Commands for warning server members of misconduct.'
    help = 'These commands are for moderators to keep track of infractions of server members manually.'
    slash_commands = ['list']
    nested = True

    @decorators.command(
        name='list',
        description='Get a list of warnings for a specific user.',
        icon='\N{SCROLL}'
    )
    @app_commands.describe(user='The user to fetch warnings for.')
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_list_command(self, interaction: Interaction, user: discord.User = None) -> None:
        if user:
            warns = await self.bot.db.warns.get_all_for_user_in_guild(user, interaction.guild)
        else:
            warns = await self.bot.db.warns.get_all_for_guild(interaction.guild)

        if len(warns) > 0:
            menu = Menu(
                MenuPageList(
                    factory=self.bot.embeds,
                    items=[f'`{w.id}:` `{w.user_name + "` - `" if not user else ""}{w.reason}`' for w in warns],
                    title=f'{user if user else interaction.guild}\'s Warnings',
                    per_page=5,
                ),
                interaction,
                ephemeral=True
            )

            await menu.start()
        else:
            if user:
                emb = self.bot.embeds.get(description=f'{user.mention} has no warnings.')
            else:
                emb = self.bot.embeds.get(description=f'`{interaction.guild}` has no warnings.')
            await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='delete',
        description='Deletes a warning by its id.',
        icon='\N{PUT LITTER IN ITS PLACE SYMBOL}'
    )
    @app_commands.describe(id='The ID of the warning to delete.')
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_delete_command(self, interaction: Interaction, id: app_commands.Range[int, 1]) -> None:
        warn = await self.bot.db.warns.get_by_id(id)

        if warn and await self.bot.db.warns.delete_by_id(id):
            emb = self.bot.embeds.get(
                title='Warning Deleted',
                fields=[
                    {
                        'name': 'User',
                        'value': warn.user_name
                    },
                    {
                        'name': 'Warned By',
                        'value': warn.warned_by_name
                    },
                    {
                        'name': 'Reason',
                        'value': warn.reason
                    }
                ]
            )
            await interaction.response.send_message(embed=emb)
        else:
            emb = self.bot.embeds.get(
                description=f'No warning with ID `{id}` was found to delete.'
            )
            await interaction.response.send_message(embed=emb)
