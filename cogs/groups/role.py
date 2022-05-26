from typing import cast

import discord
from discord import app_commands

from templates import Group, Interaction, Permission, Emoji, Confirmation, Bot
from templates import decorators, transformers


class Role(Group, name='role'):
    description = 'Commands for assigning, removing, and updating roles.',
    help = 'These commands are meant for use by moderators, and likely will not be available to normal users.'
    bot: Bot

    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    # ---------- App Commands ----------
    @decorators.command(
        name='give',
        description='Gives a role to a user.',
        icon='\N{HEAVY PLUS SIGN}'
    )
    @app_commands.describe(
        role='The role to assign to the user.',
        user='The user to give the role to. Leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_give_command(
            self,
            interaction: Interaction,
            role: discord.Role,
            user: discord.Member = None
    ) -> None:
        if not user:
            user = interaction.user

        if role in user.roles:
            emb = self.bot.embeds.get(description=f'{user.mention} already has the {role.mention} role.')
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        await user.add_roles(role)
        emb = self.bot.embeds.get(description=f'Gave {role.mention} to {user.mention}.')
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='take',
        description='Takes a role from a user.',
        icon='\N{HEAVY MINUS SIGN}'
    )
    @app_commands.describe(
        role='The role to take from the user.',
        user='The user to take the role from. Leave blank for yourself.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_take_command(
            self,
            interaction: Interaction,
            role: discord.Role,
            user: discord.Member = None
    ) -> None:
        if not user:
            user = interaction.user

        if role not in user.roles:
            emb = self.bot.embeds.get(description=f'{user.mention} does not have the {role.mention} role.')
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        await user.remove_roles(role)
        emb = self.bot.embeds.get(description=f'Took {role.mention} from {user.mention}.')
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
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
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_bulkgive_command(
            self,
            interaction: Interaction,
            role: discord.Role,
            bulk_type: app_commands.Choice[int]
    ) -> None:
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

        emb = self.bot.embeds.get(
            description=f'Gave {role.mention} to {count_success} {type_str}.' +
                        "" if count_fail == 0 else f"\n\nFailed to give the role to {count_fail} users."
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
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
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_bulktake_command(
            self,
            interaction: Interaction,
            role: discord.Role,
            bulk_type: app_commands.Choice[int]
    ) -> None:
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

        emb = self.bot.embeds.get(
            description=f'Took {role.mention} from {count_success} {type_str}.' +
                        "" if count_fail == 0 else f"\n\nFailed to take the role from {count_fail} users."
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='create',
        description='Creates a role.',
    )
    @app_commands.describe(
        name='The name of the role to create.',
        color='The color to use for the role. Should be a hex value (`#ffffff`) or an RGB tuple (`50,200,255`). Defaults to #000000.',
        display_separate='Whether to show the role\'s members separately on the member list. Defaults to False.',
        icon='The icon to use for the role. Defaults to None.',
        mentionable='Whether the role can be mentioned by `@everyone`. Defaults to False.',
        permissions='The permissions to enable for the role. All other permissions will be disabled. Defaults to no permissions enabled.',
        reason='The reason for creating the role, which appears in the server audit log. Defaults to None.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_create_command(
            self,
            interaction: discord.Interaction,
            name: str,
            color: app_commands.Transform[discord.Color, transformers.ColorTransformer] = None,
            display_separate: bool = False,
            icon: app_commands.Transform[Emoji, transformers.EmojiTransformer] = None,
            mentionable: bool = False,
            permissions: app_commands.Transform[Permission, transformers.PermissionTransformer] = None,
            reason: str = None
    ) -> None:
        color = cast(discord.Color, color or discord.Color.default())
        icon = cast(Emoji, icon)
        permissions = cast(Permission, permissions)

        cur = discord.utils.get(interaction.guild.roles, name=name)
        if cur:
            await interaction.response.send_message(
                f'A role with the name {cur.mention} already exists.',
                ephemeral=True
            )
            return

        permissions = permissions.scheme if permissions else discord.utils.MISSING

        if icon:
            if 'ROLE_ICONS' not in interaction.guild.features:
                emb = self.bot.embeds.get(
                    description='This server does not have permission to use role icons. This is a Nitro Boost perk.',
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

            if icon.is_custom:
                if icon.is_known:
                    if not icon.animated:
                        icon = await icon.discord_emoji.read()
                    else:
                        emb = self.bot.embeds.get(
                            description=f'Cannot use animated emojis for role icons. Please select a static emoji.',
                            color=discord.Color.orange()
                        )
                        await interaction.response.send_message(embed=emb, ephemeral=True)
                        return
                else:
                    emb = self.bot.embeds.get(
                        description=f'Cannot access {icon} to use for the role. Please pick a global emoji, or an emoji in this server.',
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=emb, ephemeral=True)
                    return
            else:
                icon = icon.name

        role = await interaction.guild.create_role(
            name=name,
            permissions=permissions,
            color=color,
            hoist=display_separate,
            display_icon=icon,
            mentionable=mentionable,
            reason=reason
        )

        emb = self.bot.embeds.get(
            title='Role Created',
            description=role.mention,
            color=role.color,
            thumbnail=role.display_icon,
            fields=[
                {
                    "name": "ID",
                    "value": f"`{role.id}`"
                },
                {
                    "name": "Created",
                    "value": discord.utils.format_dt(role.created_at, 'R')
                }
            ]
        )

        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='edit',
        description='Edits a role.',
    )
    @app_commands.describe(
        role='The role to edit.',
        name='The name to change the role to.',
        color='The color to change for the role. Should be a hex value (`#ffffff`) or an RGB tuple (`50,200,255`).',
        display_separate='Whether to show the role\'s members separately on the member list.',
        icon='The icon to change the role to.',
        mentionable='Whether the role can be mentioned by `@everyone`.',
        reason='The reason for editing the role, which appears in the server audit log. Defaults to None.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_edit_command(
            self,
            interaction: discord.Interaction,
            role: discord.Role,
            name: str = None,
            color: app_commands.Transform[discord.Color, transformers.ColorTransformer] = None,
            display_separate: bool = None,
            icon: app_commands.Transform[Emoji, transformers.EmojiTransformer] = None,
            mentionable: bool = None,
            reason: str = None
    ) -> None:
        color = cast(discord.Color, color)
        icon = cast(Emoji, icon)

        if icon:
            if 'ROLE_ICONS' not in interaction.guild.features:
                emb = self.bot.embeds.get(
                    description='This server does not have permission to use role icons. This is a Nitro Boost perk.',
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

            if icon.is_custom:
                if icon.is_known:
                    if not icon.animated:
                        icon = await icon.discord_emoji.read()
                    else:
                        emb = self.bot.embeds.get(
                            description=f'Cannot use animated emojis for role icons. Please select a static emoji.',
                            color=discord.Color.orange()
                        )
                        await interaction.response.send_message(embed=emb, ephemeral=True)
                        return
                else:
                    emb = self.bot.embeds.get(
                        description=f'Cannot access {icon} to use for the role. Please pick a global emoji, or an emoji in this server.',
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=emb, ephemeral=True)
                    return
            else:
                icon = icon.name

        role = await role.edit(
            name=name if name else role.name,
            color=color if color else role.color,
            hoist=display_separate if display_separate is not None else role.hoist,
            display_icon=icon if icon else role.display_icon,
            mentionable=mentionable if mentionable is not None else role.mentionable,
            reason=reason
        )

        emb = self.bot.embeds.get(
            title='Role Edited',
            description=role.mention,
            color=role.color,
            thumbnail=role.display_icon,
            fields=[
                {
                    "name": "ID",
                    "value": f"`{role.id}`"
                },
                {
                    "name": "Edited",
                    "value": discord.utils.format_dt(discord.utils.utcnow(), 'R')
                }
            ]
        )

        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='delete',
        description='Deletes a role.'
    )
    @app_commands.describe(role='The role to delete.', reason='The reason for deleting the role.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_delete_command(self, interaction: Interaction, role: discord.Role, reason: str = None):
        confirmation = Confirmation(
            user=interaction.user,
            interaction=interaction,
            msg=self.bot.embeds.get(
                title=f'Delete the "{role.name}" role?',
                description=f'This action cannot be undone.\n{role.mention} has `{len(role.members)}` members currently.'
            )
        )
        res = await confirmation.get_response()

        if res:
            await role.delete(reason=reason)
            emb = self.bot.embeds.get(
                title=f'"{role.name}" Role Deleted',
                fields=[
                    {"name": "Deleted By", "value": interaction.user.mention},
                    {"name": "Reason", "value": reason}
                ]
            )
            await interaction.edit_original_message(embed=emb, view=None)
        else:
            await interaction.delete_original_message()
            emb = self.bot.embeds.get(description=f'Cancelled {role.mention} deletion.')
            await interaction.followup.send(embed=emb, ephemeral=True)

    @decorators.command(
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
            interaction: Interaction,
            role: discord.Role,
            permission: app_commands.Transform[Permission, transformers.PermissionTransformer],
            value: bool = None
    ) -> None:
        permission = cast(Permission, permission)
        perms = permission.permissions
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

            await interaction.response.send_message(embed=emb)
        else:
            emb = self.bot.embeds.get(
                description=f'The {role.mention} role already has `{permission.flag}` permissions set to `{value}`.'
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='color',
        description='Sets the color of a given role.',
        icon='\N{ARTIST PALETTE}',
        help='Accepts a range of default colors, a random color, a hex code string like `#ffffff` or `#fff`, '
             'or an rgb tuple, like `123, 234, 200`.'
    )
    @app_commands.describe(
        role='The role to change the color for.',
        color='The color to change the role to.'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def role_color_command(
            self,
            interaction: Interaction,
            role: discord.Role,
            color: app_commands.Transform[discord.Color, transformers.ColorTransformer]
    ) -> None:
        color = cast(discord.Color, color)
        if color == role.color:
            await interaction.response.send_message(
                f'`{color}` is already the color for the {role.mention} role.',
                ephemeral=True
            )
        await role.edit(color=color)
        emb = self.bot.embeds.get(
            description=f'Updated color for {role.mention} to `{color}`.',
            color=color
        )
        await interaction.response.send_message(embed=emb)
