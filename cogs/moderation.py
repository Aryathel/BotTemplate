"""
TODO:
    Command Implementations:
        - Warns:
            - Warn member
            - View member warnings
            - Set warning limit before ban
        - Massban (?) [Takes a series of optional arguments to ban users by. I don't see a need for this rn.]
        - Clean (?) [Removes messages from the bot by count and location.]
        - Remove (?) [Removes messages meeting a certain criteria.]
    Listener Implementations:
        - Raid protection (?) [Need to look into a clean way of doing this.]
        - Spam (?) [Same as above for this. Setting rules by @mentions or regular messages seems reasonable.]
"""

from datetime import timedelta
from typing import Union, List, cast, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from templates import Bot, Cog, Interaction
from templates import decorators, transformers
from utils import LogType, clamp, Menu, MenuPageList

from .groups.role import Role
from .groups.warn import Warn
from .groups.reactionrole import ReactionRole
from .groups.embeds import Embeds


# ---------- Autocompletion functions. ----------
async def banned_users_autocomplete(
        interaction: Interaction,
        current: str
) -> List[app_commands.Choice[str]]:
    opts = await interaction.client.db.bans.get_all_active_ban_users_for_guild(interaction.guild, current)
    return [
        app_commands.Choice(name=opt.user_name, value=opt.user_name)
        for opt in opts
    ]


class ModerationCog(Cog, name="moderation"):
    name = "Moderation"
    description = "Server moderation commands."
    icon = "\N{SHIELD}"

    role: Role
    warn: Warn
    reactionrole: ReactionRole
    embeds: Embeds

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.role = Role(bot=self.bot)
        self.warn = Warn(bot=self.bot)
        self.reactionrole = ReactionRole(bot=self.bot)
        self.embeds = Embeds(bot=self.bot)
        self.slash_commands = [
            'setnick', 'bans', 'ban', 'unban', 'warn',
            self.role, self.warn, self.reactionrole, self.embeds
        ]

        self.moderation_task.start()

    def cog_unload(self) -> None:
        super().cog_unload()

        self.moderation_task.stop()

    # ---------- App Commands ----------
    @decorators.command(
        name='newmembers',
        description='Get\'s the newest members who have joined the server.',
        help='The number of members returned must be between 5 and 25, inclusive.'
    )
    @app_commands.describe(count='The number of users to fetch, no more than 25.')
    @app_commands.guild_only()
    async def newmembers_command(self, interaction: Interaction, count: int = 5) -> None:
        count = clamp(count, 5, 25)

        members = sorted(
            interaction.guild.members,
            key=lambda m: m.joined_at or interaction.guild.created_at,
            reverse=True
        )[:count]

        emb = self.bot.embeds.get(
            title=f'{len(members)} Newest Members',
            description='\n'.join([f'{i+1}: {m.mention}' for i, m in enumerate(members)])
        )

        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name="setnick",
        description="Sets the nickname of a user in the server."
    )
    @app_commands.describe(
        nickname="The nickname to set, or leave blank to clear the user's nickname.",
        user='The user to set the nickname of, or leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(manage_nicknames=True)
    async def setnick_command(
            self,
            interaction: Interaction,
            user: discord.Member = None,
            nickname: str = None
    ) -> None:
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

    @decorators.command(
        name='kick',
        description='Kicks a user from the guild.',
        icon='\N{WOMANS BOOTS}'
    )
    @app_commands.describe(
        user='The user to kick from the server.',
        reason='The reason for kicking the user.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def kick_command(self, interaction: Interaction, user: discord.Member, reason: str = None):
        await interaction.guild.kick(user, reason=f'Moderator: "{interaction.user}"\nReason: "{reason}"')
        self.bot.log(f'"{interaction.user}" kicked "{user}" from "{interaction.guild}"')
        emb = self.bot.embeds.get(
            title=f'Kicked {user}',
            fields=[
                {
                    "name": "Moderator",
                    "value": interaction.user.mention
                },
                {
                    "name": "Reason",
                    "value": reason,
                    "inline": False
                }
            ],
            thumbnail=user.display_avatar.url
        )
        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='mute',
        description='Prevents a user from doing anything for a short time.',
        icon='\N{SPEAKER WITH CANCELLATION STROKE}',
        help='This includes prevention of sending messages, reacting to messages, joining voice channels, or joining video calls.'
    )
    @app_commands.describe(
        user='The user to mute.',
        duration='The length of time to mute the user for.',
        reason='The reason for muting the user.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def mute_command(
            self,
            interaction: Interaction,
            user: discord.Member,
            duration: app_commands.Transform[timedelta, transformers.TimeDurationTransformer],
            reason: str = None
    ) -> None:
        duration = cast(timedelta, duration)
        await user.timeout(duration, reason=f'Moderator: "{interaction.user}"\nReason: "{reason}"')
        emb = self.bot.embeds.get(
            description=f'{user.mention} muted until {discord.utils.format_dt(discord.utils.utcnow() + duration, "R")}'
        )
        if reason is not None:
            emb.add_field(
                name='Reason',
                value=reason
            )
        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='unmute',
        description='Unmute a user.',
        icon='\N{SPEAKER WITH ONE SOUND WAVE}'
    )
    @app_commands.describe(user='The user to unmute.', reason='The reason for unmuting the user.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def unmute_command(
            self,
            interaction: Interaction,
            user: discord.Member,
            reason: str = None
    ) -> None:
        if not user.is_timed_out():
            emb = self.bot.embeds.get(description=f'{user.mention} is not currently muted.')
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        await user.edit(timed_out_until=None, reason=f'Moderator: "{interaction.user}"\nReason: "{reason}"')
        emb = self.bot.embeds.get(
            description=f'{user.mention} unmuted'
        )
        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='warn',
        description='Warns a user and logs the infraction.',
        icon='\N{WARNING SIGN}'
    )
    @app_commands.describe(
        user='The user to warn.',
        reason='The reason for the warning.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_command(self, interaction: Interaction, user: discord.User, reason: str) -> None:
        id = await self.bot.db.warns.insert(user, interaction.guild, interaction.user, reason)

        emb = self.bot.embeds.get(
            title=f'Warned {user}',
            thumbnail=user.display_avatar.url,
            fields=[
                {
                    'name': 'ID',
                    'value': id,
                    'inline': False,
                },
                {
                    'name': 'Reason',
                    'value': reason,
                    'inline': False,
                }
            ]
        )

        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='ban',
        description='Bans a user from the server.',
        icon='\N{NO ENTRY SIGN}'
    )
    @app_commands.describe(
        user='The user to ban.',
        duration='The length of time to ban the user, something like "2d12h", but accepts a variety of inputs.',
        reason='The reason for banning the user.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(
            self,
            interaction: Interaction,
            user: discord.Member,
            duration: app_commands.Transform[timedelta, transformers.TimeDurationTransformer] = None,
            reason: str = None
    ) -> None:
        # Modal ban form for future use with context_menus as well.
        # await interaction.response.send_modal(BanForm(user=user, bot=self.bot))

        if duration is not None:
            duration = cast(timedelta, duration)

        await user.ban(reason=f'Moderator: "{interaction.user}" Reason: "{reason}"')

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

        if duration is not None:
            unban_date = interaction.created_at + duration
            emb.add_field(
                name="Unbanned",
                value=discord.utils.format_dt(unban_date, 'R')
            )

        await self.bot.db.bans.insert(
            user=user,
            guild=interaction.guild,
            banner=interaction.user,
            duration=duration,
            reason=reason
        )
        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='softban',
        description='Softbans a user.',
        icon='\N{NO ENTRY SIGN}',
        help='Bans a user, deleting recent messages from them and removing them from the server, then unbans them immediately.'
    )
    @app_commands.describe(
        user='The user to ban.',
        reason='The reason for softbanning the user.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(
            self,
            interaction: Interaction,
            user: discord.Member,
            reason: str = None
    ) -> None:
        await user.ban(reason=f'Moderator: "{interaction.user}" Reason: "{reason}"')
        await user.unban(reason=f'Moderator: "{interaction.user}" Reason: "{reason}"')

        emb = self.bot.embeds.get(
            title=f'Softbanned {user}',
            thumbnail=user.display_avatar.url,
            fields=[
                {
                    "name": "Reason",
                    "value": reason,
                    "inline": False
                }
            ]
        )

        await self.bot.db.bans.insert(
            user=user,
            guild=interaction.guild,
            banner=interaction.user,
            duration=None,
            reason=reason,
            active=False
        )

        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='multiban',
        description='Ban multiple users at once.'
    )
    @app_commands.describe(
        users='The users to ban.',
        duration='The length of time to ban the users.',
        reason='The reason for banning these users.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def multiban(
            self,
            interaction: Interaction,
            users: app_commands.Transform[List[discord.Member], transformers.MultiMemberTransformer],
            duration: app_commands.Transform[timedelta, transformers.TimeDurationTransformer] = None,
            reason: str = None
    ) -> None:
        users = cast(List[discord.Member], users)
        duration = cast(Optional[timedelta], duration)

        for user in users:
            await interaction.guild.ban(user, reason=f'Moderator: "{interaction.user}" Reason: "{reason}"')

        emb = self.bot.embeds.get(
            title=f'Banned Members',
            description=f'{", ".join([user.mention for user in users])}',
            fields=[
                {
                    "name": "Reason",
                    "value": reason,
                    "inline": False
                }
            ]
        )

        if duration is not None:
            unban_date = interaction.created_at + duration
            emb.add_field(
                name="Unbanned",
                value=discord.utils.format_dt(unban_date, 'R')
            )

        await self.bot.db.bans.insert_multi(
            users=users,
            guild=interaction.guild,
            banner=interaction.user,
            duration=duration,
            reason=reason
        )
        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='bans',
        description='Gets a list of bans.'
    )
    @app_commands.describe(user='The user to fetch ban information for.')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_list_command(self, interaction: Interaction, user: discord.User = None) -> None:
        if not user:
            bans = await self.bot.db.bans.get_all_active_for_guild(interaction.guild)

            menu = Menu(
                MenuPageList(
                    factory=self.bot.embeds.copy().update(thumbnail=interaction.guild.icon.url),
                    items=[f'<@{b.user_id}>' for b in bans] if len(bans) > 0 else ['No users are banned in this server.'],
                    title=f'Active {interaction.guild} Bans',
                    number_items=len(bans) > 0,
                    per_page=15
                ),
                interaction=interaction,
                delete_on_quit=False
            )

            await menu.start()
        else:
            bans = await self.bot.db.bans.get_all_for_user_in_guild(user, interaction.guild)
            ban_cur = await self.bot.db.bans.get_active_for_user_in_guild(user, interaction.guild)
            recent = await self.bot.db.bans.get_most_recent_for_user(user)
            global_bans = await self.bot.db.bans.get_all_for_user(user)

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
                    },
                    {
                        "name": "Most Recent Ban",
                        "value": discord.utils.format_dt(recent, 'R') if recent else 'None',
                        "inline": True
                    }
                ],
                thumbnail=user.display_avatar.url
            )
            if ban_cur:
                emb.add_field(
                    name='Unban Date',
                    value=discord.utils.format_dt(ban_cur.unban_date, 'R') if ban_cur.unban_date else '`Never`'
                )
            try:
                guild_ban = await interaction.guild.fetch_ban(user)
                emb.add_field(
                    name='Active Ban Reason',
                    value=guild_ban.reason
                )
            except discord.NotFound:
                pass

            await interaction.response.send_message(embed=emb)

    @decorators.command(name='unban', description='Unbans a banned user.')
    @app_commands.describe(user='The user to unban.', reason='The reason for unbanning a user.')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.autocomplete(user=banned_users_autocomplete)
    async def unban_command(self, interaction: Interaction, user: str, reason: str = None) -> None:
        ban = await self.bot.db.bans.get_active_for_username_in_guild(user, interaction.guild)
        if ban:
            user = await self.bot.fetch_user(ban.user_id)
            if user:
                try:
                    await interaction.guild.unban(
                        user,
                        reason=f'{interaction.user} requested the unban of {user}: {reason}.'
                    )
                    emb = self.bot.embeds.get(description=f'Unbanned {user.mention}.')
                    await interaction.response.send_message(embed=emb, ephemeral=True)

                except discord.NotFound:
                    await self.bot.db.bans.deactivate_by_id(id=ban.ban_id)
                    emb = self.bot.embeds.get(
                        description=f'Could not unban {user.mention}. They likely have already been manually unbanned.'
                    )
                    await interaction.response.send_message(embed=emb, ephemeral=True)
            else:
                emb = self.bot.embeds.get(
                    description='That user could not be found. They likely have deleted their account.'
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
        else:
            emb = self.bot.embeds.get(
                description='My apologies, it seems that something has gone wrong with this request,'
                            ' and the ban you requested to remove could not be found.'
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)

    # ---------- App Command Error Handlers ------------
    @setnick_command.error
    async def setnick_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, discord.Forbidden):
            emb = self.bot.embeds.get(
                description='I am not able to change that user\'s nickname.',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            interaction.extras['handled'] = True

    @ban_command.error
    async def ban_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, discord.Forbidden):
            emb = self.bot.embeds.get(
                description='I am not able to ban that user.',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            interaction.extras['handled'] = True
        elif isinstance(error, app_commands.TransformerError):
            emb = self.bot.embeds.get(
                description='I cannot find that member. They may have already left the server/been banned.',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            interaction.extras['handled'] = True

    # ---------- Listeners ----------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]) -> None:
        self.bot.log(f'Banned {user} in "{guild}"')
        ban = await guild.fetch_ban(user)
        active_ban = await self.bot.db.bans.get_active_for_user_in_guild(user, guild)
        if not (ban and active_ban and (active_ban.ban_ts - discord.utils.utcnow()).total_seconds() < 60):
            await self.bot.db.bans.insert(
                user=user,
                guild=guild,
                banner=None,
                duration=None,
                reason=ban.reason
            )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        self.bot.log(f'Unbanned {user} in "{guild}"')
        await self.bot.db.bans.deactivate_all_for_user_in_guild(user, guild)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if not before.is_timed_out() and after.is_timed_out():
            self.bot.log(f'"{after}" was muted in "{after.guild}" until {after.timed_out_until}')
        elif before.is_timed_out() and not after.is_timed_out():
            self.bot.log(f'"{after}" unmuted in "{after.guild}"')

    # ---------- Tasks ----------
    @tasks.loop(minutes=1)
    async def moderation_task(self) -> None:
        try:
            # Handle unbanning people.
            bans = await self.bot.db.bans.get_all_active()
            for ban in bans:
                if ban.actionable:
                    guild = await self.bot.fetch_guild(ban.guild_id)
                    if guild:
                        user = await self.bot.fetch_user(ban.user_id)
                        if user:
                            try:
                                await guild.unban(user, reason='The timer on the ban has ended.')
                            except discord.NotFound:
                                await self.bot.db.bans.deactivate_by_id(id=ban.ban_id)
        except Exception as error:
            self.bot.log(
                f'Unhandled "{type(error).__name__}" in background task "moderation_task"',
                log_type=LogType.error,
                error=error,
                divider=True
            )

    @moderation_task.before_loop
    async def before_mod_check(self):
        await self.bot.wait_until_ready()


async def setup(bot: Bot):
    cog = ModerationCog(bot)
    await bot.add_cog(cog, guilds=[bot.GUILD])
    await bot.add_cog(cog.role, guilds=[bot.GUILD])
    await bot.add_cog(cog.warn, guilds=[bot.GUILD])
    await bot.add_cog(cog.reactionrole, guilds=[bot.GUILD])
    await bot.add_cog(cog.embeds, guilds=[bot.GUILD])
