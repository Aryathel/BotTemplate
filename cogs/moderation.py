from datetime import timedelta
from typing import Union, List

import discord
from discord import app_commands
from discord.ext import commands, tasks

from custom_types import TimeDuration, TimeDurationTransformer, Permission, PermissionTransformer, ColorTransformer
from templates import AryaBot, AryaCog, AryaInteraction, aryacommand, AryaGroup
from utils import LogType

debug = AryaBot.debug


# ---------- Autocompletion functions. ----------
async def banned_users_autocomplete(interaction: AryaInteraction,
                                    current: str) -> List[app_commands.Choice[str]]:
    opts = await interaction.client.db.bans.get_all_active_ban_users_for_guild(interaction.guild, current)
    return [
        app_commands.Choice(name=opt.user_name, value=opt.user_name)
        for opt in opts
    ]


class ModerationCog(AryaCog, name="moderation"):
    name = "Moderation"
    description = "Server moderation commands."
    icon = "\N{SHIELD}"
    slash_commands = sorted(['setnick', 'bans', 'ban', 'unban', 'role'])

    role = AryaGroup(
        name='role',
        description='Commands for assigning, removing, and updating roles.',
        help='These commands are meant for use by moderators, and likely will not be available to normal users.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.moderation_task.start()

    # ---------- App Commands ----------
    @role.command(
        name='give',
        description='Gives a role to a user.',
        icon='\N{HEAVY PLUS SIGN}'
    )
    @app_commands.describe(
        role='The role to assign to the user.',
        user='The user to give the role to. Leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def role_give_command(self, interaction: AryaInteraction, role: discord.Role, user: discord.Member = None):
        if not user:
            user = interaction.user

        if role in user.roles:
            await interaction.response.send_message(f'{user.mention} already has the {role.mention} role.',
                                                    ephemeral=True)
            return

        await user.add_roles(role)
        await interaction.response.send_message(f'Gave {role.mention} to {user.mention}.')

    @role.command(
        name='take',
        description='Takes a role from a user.',
        icon='\N{HEAVY MINUS SIGN}'
    )
    @app_commands.describe(
        role='The role to take from the user.',
        user='The user to take the role from. Leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def role_take_command(self, interaction: AryaInteraction, role: discord.Role, user: discord.Member = None):
        if not user:
            user = interaction.user

        if role not in user.roles:
            await interaction.response.send_message(f'{user.mention} does not have the {role.mention} role.',
                                                    ephemeral=True)
            return

        await user.remove_roles(role)
        await interaction.response.send_message(f'Took {role.mention} from {user.mention}.')

    @role.command(
        name='bulkgive',
        description='Gives a role to multiple users at once.',
        icon='\N{HEAVY PLUS SIGN}'
    )
    @app_commands.describe(
        role='The role to give to the selected group.',
        bulk_type='The type of users to give the role to.'
    )
    @app_commands.rename(bulk_type='type')
    @app_commands.choices(bulk_type=[
        app_commands.Choice(name='All Users', value=1),
        app_commands.Choice(name='Bots', value=2),
        app_commands.Choice(name='Humans', value=3)
    ])
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def role_bulkgive_command(self, interaction: AryaInteraction, role: discord.Role,
                                    bulk_type: app_commands.Choice[int]):
        count_success = 0
        count_fail = 0
        type_str = None
        if bulk_type.value == 1:
            type_str = 'users'
            for member in interaction.guild.members:
                try:
                    await member.add_roles(role)
                    count_success += 1
                except discord.Forbidden:
                    count_fail += 1
        elif bulk_type.value == 2:
            type_str = 'bots'
            for member in interaction.guild.members:
                if member.bot:
                    try:
                        await member.add_roles(role)
                        count_success += 1
                    except discord.Forbidden:
                        count_fail += 1
        elif bulk_type.value == 3:
            type_str = 'humans'
            for member in interaction.guild.members:
                if not member.bot:
                    try:
                        await member.add_roles(role)
                        count_success += 1
                    except discord.Forbidden:
                        count_fail += 1

        await interaction.response.send_message(
            f'Gave {role.mention} to {count_success} {type_str}.{"" if count_fail == 0 else f" Failed to give the role to {count_fail} users."}')

    @role.command(
        name='bulktake',
        description='Takes a role to multiple users at once.',
        icon='\N{HEAVY MINUS SIGN}'
    )
    @app_commands.describe(
        role='The role to take from the selected group.',
        bulk_type='The type of users to take the role from.'
    )
    @app_commands.rename(bulk_type='type')
    @app_commands.choices(bulk_type=[
        app_commands.Choice(name='All Users', value=1),
        app_commands.Choice(name='Bots', value=2),
        app_commands.Choice(name='Humans', value=3)
    ])
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def role_bulktake_command(self, interaction: AryaInteraction, role: discord.Role,
                                    bulk_type: app_commands.Choice[int]):
        count_success = 0
        count_fail = 0
        type_str = None
        if bulk_type.value == 1:
            type_str = 'users'
            for member in interaction.guild.members:
                try:
                    await member.remove_roles(role)
                    count_success += 1
                except discord.Forbidden:
                    count_fail += 1
        elif bulk_type.value == 2:
            type_str = 'bots'
            for member in interaction.guild.members:
                if member.bot:
                    try:
                        await member.remove_roles(role)
                        count_success += 1
                    except discord.Forbidden:
                        count_fail += 1
        elif bulk_type.value == 3:
            type_str = 'humans'
            for member in interaction.guild.members:
                if not member.bot:
                    try:
                        await member.remove_roles(role)
                        count_success += 1
                    except discord.Forbidden:
                        count_fail += 1

        await interaction.response.send_message(
            f'Took {role.mention} from {count_success} {type_str}.{"" if count_fail == 0 else f" Failed to take the role from {count_fail} users."}')

    @role.command(
        name='permissions',
        description='Allows changing a specific permission for a certain role.'
    )
    @app_commands.describe(
        role='The role to change the permissions for.',
        permission='The permission to update for the role.',
        value='The value to set the permission to for the role.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_permissions_command(
            self,
            interaction: AryaInteraction,
            role: discord.Role,
            permission: app_commands.Transform[Permission, PermissionTransformer],
            value: bool = None
    ):
        perms: List[str] = permission.permissions

        cur = role.permissions

        updated = {}
        for flag in perms:
            if not getattr(cur, flag) == value:
                setattr(cur, flag, value)
                updated[flag] = value

        if len(updated) > 0:
            await role.edit(permissions=cur)

            emb = self.bot.embeds.get(
                title='Role Permissions Updated',
                description=f'Updated permissions to `{value}` for the {role.mention} role.\n\n```\n' +
                            '\n'.join(f'{flag}' for flag in sorted(list(updated.keys()))) + '```',
                color=role.color
            )

            await interaction.response.send_message(
                embed=emb
            )
        else:
            await interaction.response.send_message(
                f'The {role.mention} role already has `{permission.flag}` permissions set to `{value}`.',
                ephemeral=True
            )

    @role.command(
        name='color',
        description='Sets the color of a given role.',
        icon='\N{ARTIST PALETTE}',
        help='Accepts a range of default colors, a random color, a hex code string like `#ffffff` or `#fff`, '
             'or an rgb value, like `123, 234, 200`.'
    )
    @app_commands.describe(
        role='The role to change the color for.',
        color='The color to change the role to.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_color_command(self, interaction: AryaInteraction, role: discord.Role, color: app_commands.Transform[discord.Color, ColorTransformer]):
        color: discord.Color = color
        if color == role.color:
            await interaction.response.send_message(
                f'`{color}` is already the color for the {role.mention} role.',
                ephemeral=True
            )
        await role.edit(color=color)
        await interaction.response.send_message(f'Updated color for {role.mention} to `{color}`.')

    @aryacommand(
        name="setnick",
        description="Sets the nickname of a user in the server."
    )
    @app_commands.describe(
        nickname="The nickname to set, or leave blank to clear the user's nickname.",
        user='The user to set the nickname of, or leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(manage_nicknames=True)
    async def setnick_command(self, interaction: AryaInteraction, user: discord.Member = None,
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

    @aryacommand(name='ban', description='Bans a user from the server.')
    @app_commands.describe(
        user='The user to ban.',
        duration='The length of time to ban the user, something like "2d12h", but accepts a variety of inputs.'
    )
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(
            self,
            interaction: AryaInteraction,
            user: discord.Member,
            duration: app_commands.Transform[TimeDuration, TimeDurationTransformer] = None,
            reason: str = None
    ):
        # Modal ban form for future use with context_menus as well.
        # await interaction.response.send_modal(BanForm(user=user, bot=self.bot))

        if duration is not None:
            duration: timedelta = duration.duration

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
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @aryacommand(
        name='bans',
        description='Gets a list of bans.'
    )
    @app_commands.describe(user='The user to fetch ban information for.')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_list_command(self, interaction: AryaInteraction, user: discord.User = None):
        if not user:
            bans = await self.bot.db.bans.get_all_active_for_guild(interaction.guild)

            emb = self.bot.embeds.get(
                title=f'Active {interaction.guild} Bans',
                description='\n'.join(f'<@{b.user_id}>' for b in bans) if len(
                    bans) > 0 else 'No users are banned in this server.',
                thumbnail=interaction.guild.icon.url
            )

            await interaction.response.send_message(embed=emb)
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
                    value=discord.utils.format_dt(ban_cur.unban_date, 'R') if ban_cur.unban_date else '`Never`',
                    inline=True
                )
            try:
                guild_ban = await interaction.guild.fetch_ban(user)
                emb.add_field(
                    name='Active Ban Reason',
                    value=guild_ban.reason,
                    inline=True
                )
            except discord.NotFound:
                pass

            await interaction.response.send_message(embed=emb)

    @aryacommand(name='unban', description='Unbans a banned user.')
    @app_commands.describe(user='The user to unban.', reason='The reason for unbanning a user.')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.autocomplete(user=banned_users_autocomplete)
    async def unban_command(self, interaction: AryaInteraction, user: str, reason: str = None):
        ban = await self.bot.db.bans.get_active_for_username_in_guild(user, interaction.guild)
        if ban:
            user = await self.bot.fetch_user(ban.user_id)
            if user:
                try:
                    await interaction.guild.unban(user, reason=f'{interaction.user} requested the unban of {user}.')
                    await interaction.response.send_message(f'Unbanned {user.mention}.', ephemeral=True)

                except discord.NotFound:
                    await self.bot.db.bans.deactivate_by_id(id=ban.ban_id)
                    await interaction.response.send_message(
                        f'Could not unban {user.mention}. They likely have already been manually unbanned.',
                        ephemeral=True)
            else:
                await interaction.response.send_message(
                    'That user could not be found. They likely have deleted their account.',
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                'My apologies, it seems that something has gone wrong with this request, and the ban you requested to remove could not be found.',
                ephemeral=True
            )

    # ---------- App Command Error Handlers ------------
    @setnick_command.error
    async def setnick_error(self, interaction: AryaInteraction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, discord.Forbidden):
            await interaction.response.send_message(
                'I am not able to change that user\'s nickname.',
                ephemeral=True
            )
            interaction.extras['handled'] = True

    @ban_command.error
    async def ban_error(self, interaction: AryaInteraction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, discord.Forbidden):
            await interaction.response.send_message(
                'I am not able to ban that user.',
                ephemeral=True
            )
            interaction.extras['handled'] = True
        elif isinstance(error, app_commands.TransformerError):
            await interaction.response.send_message(
                'I cannot find that member. They may have already left the server/been banned.',
                ephemeral=True
            )
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


async def setup(bot: AryaBot):
    await bot.add_cog(ModerationCog(bot), guilds=[bot.GUILD])
