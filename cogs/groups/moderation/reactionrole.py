from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from templates import GroupCog, Interaction, Emoji, Message
from templates import decorators, transformers, views
from database.models.role_reaction import RoleReaction


@app_commands.guild_only()
@app_commands.checks.bot_has_permissions(moderate_members=True)
@app_commands.checks.has_permissions(moderate_members=True)
class ReactionRole(GroupCog, group_name='rr', name='role_reaction'):
    name = "Role Reaction"
    description = "Commands for creating and managing reaction roles in a server."
    help = "These commands are for use by moderators, " \
           "and require at least `moderate_members` permissions for both the bot and the user to be activated."
    slash_commands = ['add', 'remove', 'list']
    nested = True

    @decorators.command(
        name='list',
        description='Lists current role reactions for the server the command is used in.',
        icon="\N{SCROLL}"
    )
    @app_commands.rename(msg="message")
    @app_commands.describe(
        msg="A link to the message to add the reaction role to, "
            "or a role reaction ID (see `/rolereaction list`)."
    )
    async def role_reaction_list_command(
            self,
            interaction: Interaction,
            msg: app_commands.Transform[Message, transformers.MessageTransformer] = None,
    ) -> None:
        if msg:
            msg: Message = cast(Message, msg)
            if not msg.is_role_reaction:
                emb = self.bot.embeds.get(
                    description="The given message is not an active role reaction message.",
                    color=discord.Color.orange()
                )
            else:
                rrs = await self.bot.db.role_reactions.get_by_role_reaction_message_id(msg.role_reaction_msg.id)
                msgs = []
                for r in rrs:
                    r.populate(interaction)
                    msgs.append(f"{r.emoji} = {r.role.mention} `ID: {r.id}`")
                emb = self.bot.embeds.get(
                    title="Role Reaction Information",
                    url=msg.message.jump_url,
                    fields=[
                        {
                            "name": "ID",
                            "value": f'`{msg.role_reaction_msg.id}`',
                            "inline": False
                        },
                        {
                            "name": "Reactions",
                            "value": "\n".join(msgs),
                            "inline": False
                        }
                    ]
                )
            await interaction.response.send_message(embed=emb, ephemeral=True)
        else:
            rr_msgs = await self.bot.db.role_reaction_messages.get_active_by_guild(interaction.guild)
            if rr_msgs:
                msgs = []
                for r in rr_msgs:
                    channel = interaction.guild.get_channel(r.channel_id)
                    message = await channel.fetch_message(r.message_id)
                    msgs.append(f"`{r.id}` {channel.mention}: [View]({message.jump_url})")
                emb = self.bot.embeds.get(
                    title=f"{interaction.guild} Reaction Roles",
                    description='\n'.join(msgs)
                )
            else:
                emb = self.bot.embeds.get(
                    title=f"{interaction.guild} Reaction Roles",
                    description="This server has no active reaction roles."
                )
            await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name="add",
        description="Initiates the creation of a new reaction role message.",
        help="Requires `manage_roles` permissions for both the bot and the user.",
        icon="\N{HEAVY PLUS SIGN}"
    )
    @app_commands.rename(msg="message")
    @app_commands.describe(
        msg="A link to the message to add the reaction role to, "
            "or a role reaction ID (see `/rolereaction list`).",
        role="The role to give the user when the reaciton is added.",
        emoji="The reaction to trigger giving the role to the user."
    )
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_reaction_add_command(
            self,
            interaction: Interaction,
            msg: app_commands.Transform[Message, transformers.MessageTransformer],
            role: discord.Role,
            emoji: app_commands.Transform[Emoji, transformers.EmojiTransformer]
    ) -> None:
        msg: Message = cast(Message, msg)
        emoji: Emoji = cast(Emoji, emoji)

        if not emoji.is_known:
            emb = self.bot.embeds.get(
                description=f"Cannot access the `{emoji.name}` emoji. Please ensure that the emoji is either in this "
                            f"server, or is a default Discord emoji.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        if not msg.is_role_reaction:
            id = await self.bot.db.role_reaction_messages.insert(
                message_id=msg.message.id,
                channel_id=msg.message.channel.id,
                guild_id=msg.message.guild.id
            )
            rr_msg = await self.bot.db.role_reaction_messages.get_by_id(id)
        else:
            rr_msg = msg.role_reaction_msg

        rrs = await self.bot.db.role_reactions.get_by_role_reaction_message_id(rr_msg.id)
        for rr in rrs:
            if role.id == rr.role_id:
                if rr.is_custom:
                    emoji = self.bot.get_emoji(rr.emoji_id)
                else:
                    emoji = rr.emoji_name

                emb = self.bot.embeds.get(
                    description=f"The {role.mention} role already has the {emoji} role reaction assigned.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return
            elif (rr.is_custom and emoji.is_custom and rr.emoji_id == emoji.id) or \
                    (not rr.is_custom and not emoji.is_custom and rr.emoji_name == emoji.name):
                rr_role = interaction.guild.get_role(rr.role_id)
                emb = self.bot.embeds.get(
                    description=f"The {emoji} emoji is already assigned to the {rr_role.mention} role.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

        await self.bot.db.role_reactions.insert(role.id, emoji, rr_msg.id)

        rrs = await self.bot.db.role_reactions.get_by_role_reaction_message_id(rr_msg.id)
        for rr in rrs:
            rr.populate(interaction)

        rrs = sorted(rrs, key=lambda r: r.role.name)
        msg: discord.Message = msg.message

        if msg.author.id == self.bot.user.id:
            await self.update_role_reaction_message(msg, rrs)

        if rr_msg.active:
            await msg.add_reaction(emoji.usage_form)

        emb = self.bot.embeds.get(
            description=f"Role reaction added: {emoji} gives {role.mention}."
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='remove',
        description='Removes a role reaction from a message',
        help='Requires `manage_roles` and `manage_messages` permissions to use.',
        icon="\N{HEAVY MINUS SIGN}"
    )
    @app_commands.rename(msg="message")
    @app_commands.describe(
        msg="A link to the message to remove the reaction role from, "
            "or a role reaction ID (see `/rolereaction list`).",
        role="The role to remove a reaction for on the message.",
        emoji="The emoji to remove a reaction for on the message.",
    )
    @app_commands.checks.bot_has_permissions(manage_roles=True, manage_messages=True)
    @app_commands.checks.has_permissions(manage_roles=True, manage_messages=True)
    async def role_reaction_remove_command(
            self,
            interaction: Interaction,
            msg: app_commands.Transform[Message, transformers.MessageTransformer],
            role: discord.Role = None,
            emoji: app_commands.Transform[Emoji, transformers.EmojiTransformer] = None
    ) -> None:
        msg: Message = cast(Message, msg)
        emoji: Emoji = cast(Emoji, emoji)
        if not msg.is_role_reaction:
            emb = self.bot.embeds.get(
                description='This message is not a registered role reaction.',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        if not role and not emoji:
            emb = self.bot.embeds.get(
                description=f"Are you sure you want to delete all role reactions for "
                            f"[that message]({msg.message.jump_url})? Try the command again and specify either the "
                            f"`role` or `emoji` arguments to remove a single role reaction."
            )
            confirm = views.Confirmation(interaction, interaction.user, msg=emb, ephemeral=True)
            if not await confirm.get_response():
                await interaction.delete_original_response()
                return
            await self.bot.db.role_reactions.delete_by_role_reaction_message_id(msg.role_reaction_msg.id)
            await self.bot.db.role_reaction_messages.delete_by_id(msg.role_reaction_msg.id)
            await msg.message.clear_reactions()

            if msg.message.author.id == self.bot.user.id:
                await self.update_role_reaction_message(msg.message, [])

            emb = self.bot.embeds.get(description="Role reactions removed.")
            await interaction.delete_original_response(embed=emb, view=None)
            return

        rrs = await self.bot.db.role_reactions.get_by_role_reaction_message_id(msg.role_reaction_msg.id)
        for rr in rrs:
            rr.populate(interaction)
            if (rr.role and role and role.id == rr.role.id) or (emoji and rr.emoji and emoji == rr.emoji):
                await msg.message.clear_reaction(rr.emoji)
                await self.bot.db.role_reactions.delete_by_id(rr.id)
                rrs = await self.bot.db.role_reactions.get_by_role_reaction_message_id(msg.role_reaction_msg.id)
                for r in rrs:
                    r.populate(interaction)
                if not rrs:
                    self.bot.db.role_reaction_messages.delete_by_id(rr.role_reaction_message_id)
                if msg.message.author.id == self.bot.user.id:
                    await self.update_role_reaction_message(
                        msg.message,
                        rrs
                    )
                emb = self.bot.embeds.get(description="Role reaction removed.")
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

        emb = self.bot.embeds.get(
            description=f"There was no role reaction to remove for that role or emoji.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=emb)

    async def update_role_reaction_message(self, msg: discord.Message, rrs: list[RoleReaction]) -> None:
        role_list = '\n'.join(f'{r.emoji} {r.role.mention}' for r in rrs)

        emb = None
        if msg.embeds:
            emb = msg.embeds[0].copy()

            to_remove = []
            for i, field in enumerate(emb.fields):
                if field.name == 'Role Reactions':
                    to_remove.append(i)

            for i in to_remove:
                emb.remove_field(i)

            if role_list:
                emb.add_field(name="Role Reactions", value=role_list, inline=False)
        else:
            if role_list:
                emb = self.bot.embeds.get(
                    fields=[
                        {
                            "name": "Role Reactions",
                            "value": role_list,
                            "inline": False
                        }
                    ]
                )
        await msg.edit(content=msg.content, embed=emb, attachments=msg.attachments)

    @commands.Cog.listener(name='on_raw_reaction_add')
    @commands.Cog.listener(name='on_raw_reaction_remove')
    async def on_raw_reaction(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id:
            rr_msg = await self.bot.db.role_reaction_messages.get_by_message_id(payload.message_id)
            if rr_msg:
                rrs = await self.bot.db.role_reactions.get_by_role_reaction_message_id(rr_msg.id)
                role = None
                for rr in rrs:
                    if payload.emoji.is_custom_emoji() and rr.emoji_id == payload.emoji.id:
                        role = rr.role_id
                    elif rr.emoji_name == payload.emoji.name:
                        role = rr.role_id

                guild = self.bot.get_guild(rr_msg.guild_id)

                if role:
                    role = guild.get_role(role)
                    if payload.event_type == 'REACTION_ADD':
                        if role not in payload.member.roles:
                            await payload.member.add_roles(role, reason='Role reaction added.')
                    elif payload.event_type == 'REACTION_REMOVE':
                        member = guild.get_member(payload.user_id)
                        if role in member.roles:
                            await member.remove_roles(role, reason='Role reaction removed.')
                elif payload.event_type == 'REACTION_ADD':
                    channel = guild.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    await message.remove_reaction(payload.emoji, payload.member)
