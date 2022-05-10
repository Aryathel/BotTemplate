import datetime
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands, tasks

from templates.views import BanForm
from main import AryaBot
from utils.general import tdelta_from_str


class ModerationCog(commands.Cog, name="Moderation"):
    role_group = app_commands.Group(name='role', description='Commands for assigning, removing, or modifying roles.')
    bot: AryaBot = None

    def __init__(self, bot: AryaBot):
        self.bot: AryaBot = bot

    # ---------- App Commands ----------
    @app_commands.command(name="setnick", description="Sets the nickname of a user in the server.")
    @app_commands.describe(
        nickname="The nickname to set, or leave blank to clear the user's nickname.",
        user='The user to set the nickname of, or leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(manage_nicknames=True)
    async def setnick_command(self, interaction: discord.Interaction, user: discord.Member = None,
                              nickname: str = None) -> None:
        if not user:
            user = interaction.user

        nickname = None if nickname == "" else nickname

        if user.nick is not None:
            old = user.nick
        else:
            old = user.name

        await user.edit(nick=nickname)

        emb = self.bot.embeds.get(
            title='Nickname Changed',
            fields=[
                {
                    "name": "New Name",
                    "value": user.mention,
                    "inline": True
                },
                {
                    "name": "Old Name",
                    "value": old,
                    "inline": True
                }
            ],
            thumbnail=user.display_icon
        )
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name='ban', description='Bans a user from the server.')
    @app_commands.describe(
        user='The user to ban.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(self, interaction: discord.Interaction, user: discord.Member, duration: str = None,
                          reason: str = None):
        # Modal ban form for future use with context_menus as well.
        # await interaction.response.send_modal(BanForm(user=user, bot=self.bot))

        await user.ban(reason=reason)

        emb = self.bot.embeds.get(
            title=f'Banned {user}',
            thumbnail=user.display_avatar.url,
            fields=[
                {
                    "name": "Reason",
                    "value": reason,
                    "inline": False
                }
            ]
        )

        if duration:
            try:
                now = interaction.created_at
                td = tdelta_from_str(duration)
                unban_date = now + td

                emb.add_field(
                    name="Unbanned",
                    value=discord.utils.format_dt(unban_date, 'R')
                )
            except Exception as e:
                td = None
        else:
            td = None

        await self.bot.db.bans.insert(
            user=user,
            guild=interaction.guild,
            banner=interaction.user,
            duration=td,
            reason=reason
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name='bans', description='Gets a list of bans.')
    @app_commands.describe(user='The user to fetch ban information for.')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_list_command(self, interaction: discord.Interaction, user: discord.User = None):
        if not user:
            bans = await self.bot.db.bans.get_all_for_guild(interaction.guild)

            emb = self.bot.embeds.get(
                title='Active Server Bans',
                description='\n'.join(f'<@{b.user_id}>' for b in bans)
            )

            await interaction.response.send_message(embed=emb)
        else:
            bans = await self.bot.db.bans.get_all_for_user(user, interaction.guild)
            global_bans = await self.bot.db.bans.get_all_for_user_global(user)

            emb = self.bot.embeds.get(
                title=f'{user}\'s Bans',
                fields=[
                    {
                        "name": "Ban Status",
                        "value": '`Banned`' if any(b.active for b in bans) else '`Not Banned`',
                        "inline": True
                    },
                    {
                        "name": "Server Ban Count",
                        "value": len(bans),
                        "inline": True
                    },
                    {
                        "name": "Global Ban Count",
                        "value": len(global_bans),
                        "inline": True
                    }
                ],
                thumbnail=user.display_avatar.url
            )
            async for ban in interaction.guild.bans(limit=None):
                if ban.user == user:
                    emb.add_field(
                        name='Active Ban Reason',
                        value=ban.reason,
                        inline=False
                    )
            await interaction.response.send_message(embed=emb)

    # ---------- App Command Error Handlers ------------
    @setnick_command.error
    async def setnick_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, discord.Forbidden):
            await interaction.response.send_message(
                'I am not able to change that user\'s nickname.',
                ephemeral=True
            )
            interaction.extras['handled'] = True

    @ban_command.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, discord.Forbidden):
            await interaction.response.send_message(
                'I am not able to ban that user.',
                ephemeral=True
            )
            interaction.extras['handled'] = True

    # ---------- Listeners ----------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]):
        ban = await guild.fetch_ban(user)
        await self.bot.db.bans.insert(
            user=user,
            guild=guild,
            banner=None,
            duration=None,
            reason=ban.reason
        )

    # ---------- Tasks ----------
    @tasks.loop(minutes=1)
    async def check_moderation(self):
        pass

    @check_moderation.before_loop
    async def before_mod_check(self):
        await self.bot.wait_until_ready()


async def setup(bot: AryaBot):
    await bot.add_cog(ModerationCog(bot), guilds=[bot.GUILD])
