from datetime import timedelta
from typing import Union, List, Any, Optional, TYPE_CHECKING

import discord
import tweepy
from discord import app_commands
from discord.ext import commands
import emoji

from utils import tdelta_from_str, clamp, str_from_tdelta
from ..bot import Interaction, Cog
from ..commands import Command, Group
from ..types import AppCommandOptionType, COLORS, RGB_PATTERN, PERMISSION_FLAGS, \
    C_EMOJI_PATTERN, Emoji, Permission, USER_MENTION_PATTERN, Message, TWITTER_USER_PATTERN, \
    TwitterUserField
from ..errors import TransformerError

if TYPE_CHECKING:
    from database.models.twitter_monitors import TwitterMonitor


# ---------- Multiple User Argument ----------
class MultiUserTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: Any) -> List[discord.User]:
        users = []
        for match in USER_MENTION_PATTERN.findall(value):
            user = interaction.client.get_user(int(match))
            if user:
                users.append(user)
        return users


class MultiMemberTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: Any) -> List[discord.Member]:
        users = []
        for match in USER_MENTION_PATTERN.findall(value):
            member = interaction.guild.get_member(int(match))
            if member:
                users.append(member)
        return users


# ---------- Color Argument ----------
class ColorTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: str) -> discord.Color:
        if value in COLORS:
            return COLORS[value]()
        else:
            match = RGB_PATTERN.search(value)
            if match is not None:
                return discord.Color.from_rgb(
                    r=clamp(int(match.group('r')), 0, 255),
                    g=clamp(int(match.group('g')), 0, 255),
                    b=clamp(int(match.group('b')), 0, 255)
                )

            try:
                return discord.Color.from_str(value)
            except ValueError:
                raise TransformerError(
                    value=value,
                    opt_type=AppCommandOptionType.color,
                    transformer=ColorTransformer
                )

    @classmethod
    async def autocomplete(
            cls, interaction: Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        vals = []

        for kind in COLORS.keys():
            if value.lower() in kind.lower():
                vals.append(app_commands.Choice(name=kind, value=kind))
                if (value in [None, ''] and len(vals) >= 24) or len(vals) >= 25:
                    break

        if not value in [None, '']:
            vals.append(app_commands.Choice(name=value, value=value))

        return vals


# ---------- Message Argument ----------
class MessageTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: str) -> Optional[Message]:
        return await cls.message_from_string(interaction, value)

    @classmethod
    async def autocomplete(
        cls, interaction: Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        try:
            msg = await cls.message_from_string(interaction, value)
        except TransformerError:
            return []

        msg = msg.message

        choice_len = 200
        content = ""
        if msg.content:
            content = msg.content[:choice_len]
        elif msg.embeds:
            if msg.embeds[0].title:
                content = msg.embeds[0].title[:choice_len]
            elif msg.embeds[0].description:
                content = msg.embeds[0].description[:choice_len]
        else:
            content = str(msg.id)

        return [app_commands.Choice(name=content, value=value)]

    @classmethod
    async def message_from_string(cls, interaction: Interaction, value: str) -> Optional[Message]:
        ids = value.strip().rstrip('/').split('/')[-3:]
        message = None
        if len(ids) == 1:
            message = await cls.message_from_role_reaction_id(interaction, ids[0])
        elif len(ids) == 3:
            message = await cls.message_from_link(interaction, ids)

        if not message:
            raise TransformerError(
                value=value,
                opt_type=AppCommandOptionType.message,
                transformer=MessageTransformer
            )

        return message

    @classmethod
    async def message_from_role_reaction_id(cls, interaction: Interaction, id: str) -> Optional[Message]:
        try:
            id = int(id)
        except ValueError:
            return

        role_reaction_message = await interaction.client.db.role_reaction_messages.get_by_id(id)

        if not role_reaction_message:
            role_reaction_message = await interaction.client.db.role_reaction_messages.get_by_message_id(id)

        if not role_reaction_message:
            return

        if not interaction.guild.id == role_reaction_message.guild_id:
            return

        channel = interaction.guild.get_channel(role_reaction_message.channel_id)

        if not channel:
            return

        try:
            message = await channel.fetch_message(role_reaction_message.message_id)
        except discord.NotFound:
            return

        return Message(message, rr_msg=role_reaction_message)

    @classmethod
    async def message_from_link(cls, interaction: Interaction, ids: list[str]) -> Optional[Message]:
        try:
            guild_id, channel_id, message_id = (int(i) for i in ids)
        except ValueError:
            return

        if not interaction.guild.id == guild_id:
            return

        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return

        role_reaction_message = await interaction.client.db.role_reaction_messages.get_by_message_id(message_id)

        return Message(message, rr_msg=role_reaction_message)


# ---------- Permission Argument ----------
class PermissionTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: str) -> Permission:
        if value in PERMISSION_FLAGS:
            return Permission(flag=value)

        # If no permissions were found for the argument, raise an error.
        raise TransformerError(
            value=value,
            opt_type=AppCommandOptionType.permission,
            transformer=PermissionTransformer
        )

    @classmethod
    async def autocomplete(
            cls, interaction: Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        vals = []
        for opt in PERMISSION_FLAGS:
            if value.lower() in opt.lower() or value in [None, '']:
                vals.append(app_commands.Choice(name=opt, value=opt))
                if len(vals) >= 25:
                    break
        return vals


# ---------- Command Argument ----------
class CommandTransformer(app_commands.Transformer):
    @classmethod
    async def transform(
            cls,
            interaction: Interaction,
            value: str
    ) -> Union[Command, Group, Cog]:
        for opt, obj in interaction.client.command_autocomplete_list.items():
            if value.lower() == opt.lower():
                return obj
            elif isinstance(obj, Cog) and value.lower() == obj.name.lower():
                return obj

        # If no commands were found for the argument, raise an error.
        raise TransformerError(
            value=value,
            opt_type=AppCommandOptionType.command,  # type: ignore
            transformer=CommandTransformer
        )

    @classmethod
    async def autocomplete(
            cls,
            interaction: Interaction,
            value: str
    ) -> List[app_commands.Choice[str]]:
        bot: commands.Bot = interaction.client

        choices = []
        for opt, obj in bot.command_autocomplete_list.items():
            if value.lower() in opt.lower():
                choices.append(app_commands.Choice(name=opt, value=opt))
            elif isinstance(obj, commands.Cog) and value.lower() in obj.name.lower():
                choices.append(app_commands.Choice(name=opt, value=opt))

            if len(choices) >= 25:
                break

        return choices


# ---------- Time Duration Argument ----------
class TimeDurationTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> timedelta:
        try:
            duration = tdelta_from_str(value)
            return duration
        except Exception:
            pass

        # If no duration could be read from the input.
        raise TransformerError(
            value=value,
            opt_type=AppCommandOptionType.time_duration,  # type: ignore
            transformer=TimeDurationTransformer
        )

    @classmethod
    async def autocomplete(
            cls, interaction: discord.Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        try:
            duration = tdelta_from_str(value)
            res = str_from_tdelta(duration)

            return [app_commands.Choice(name=res, value=res)]

        except Exception:
            return [app_commands.Choice(name='Invalid Format', value='Invalid Format')]


# ---------- Emoji Argument ----------
class EmojiTransformer(discord.app_commands.Transformer):
    """The transformer to allow an emoji argument for a slash command.

    Takes a string input, then uses the compiled regex patterns to search for the first unicode and custom emojis.
    Whichever one comes first is then converted into a `types.Emoji` object and passed to the function.
    """

    @classmethod
    def find_emoji(cls, matches: list[dict]) -> dict:
        return matches[0] if matches else None

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> Emoji:
        # Get the first instances of either a unicode or custom emoji (these will be None if not found).
        u_emoji = cls.find_emoji(emoji.emoji_list(value))
        c_emoji = C_EMOJI_PATTERN.search(value)

        # Determine which emoji type to use.
        # If both emoji types were found, use the one which comes first.
        kind = -1
        if all([u_emoji, c_emoji]):
            kind = 0 if u_emoji['match_start'] < c_emoji.start() else 1
        elif u_emoji is not None:
            kind = 0
        elif c_emoji is not None:
            kind = 1

        # Create the emoji objects.
        if kind == 0:
            emote = Emoji(name=u_emoji['emoji'])
        elif kind == 1:
            # Extract information for a custom emoji from the regex match.
            name = c_emoji.group('name')
            if name is None:
                name = c_emoji.group('a_name')
                id = c_emoji.group('a_id')
                animated = True
            else:
                id = c_emoji.group('id')
                animated = False

            id = int(id)

            # Create the Emoji object.
            emote = Emoji(
                name=name,
                id=id,
                animated=animated,
                discord_emoji=interaction.client.get_emoji(id)
            )
        else:
            # If no emojis were found in the argument, raise an error.
            raise TransformerError(
                value=value,
                opt_type=AppCommandOptionType.emoji,  # type: ignore
                transformer=EmojiTransformer
            )

        return emote


# ---------- Twitter Transformers ----------
class TwitterUserTransformer(app_commands.Transformer):
    twitter_user_query = (
            TwitterUserField.id | TwitterUserField.name | TwitterUserField.username | TwitterUserField.description |
            TwitterUserField.profile_image_url | TwitterUserField.url
    ).query

    @classmethod
    async def transform(cls, interaction: Interaction, value: str) -> Optional[tweepy.User]:
        error = TransformerError(
            value=value,
            opt_type=AppCommandOptionType.twitter_user,
            transformer=TwitterUserTransformer
        )

        if not cls.valid_username(value):
            raise error

        res = await interaction.client.twitter.get_user(username=value.lstrip('@'), user_fields=cls.twitter_user_query)

        if not res.data:
            raise error

        return res.data

    @classmethod
    async def autocomplete(
        cls, interaction: Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        choices = []
        if value and cls.valid_username(value):
            try:
                res = await interaction.client.twitter.get_user(username=value.lstrip('@'))
            except tweepy.BadRequest:
                return []

            if res.data:
                user: tweepy.User = res.data
                response = f"{user.name} @{user.username}"
                choices.append(app_commands.Choice(name=response, value=user.username))
        return choices

    @staticmethod
    def valid_username(username: str) -> bool:
        return TWITTER_USER_PATTERN.match(username.lstrip('@'))


class TwitterMonitorTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: int) -> 'TwitterMonitor':
        res = None
        if value:
            try:
                res = await interaction.client.db.twitter_monitors.get_by_id(int(value))
            except ValueError:
                pass

        if not res:
            raise TransformerError(
                value=value,
                opt_type=AppCommandOptionType.twitter_monitor,
                transformer=TwitterMonitorTransformer
            )

        return res

    @classmethod
    async def autocomplete(
        cls, interaction: Interaction, value: int
    ) -> List[app_commands.Choice[str]]:
        choices = []
        if value:
            try:
                res = await interaction.client.db.twitter_monitors.get_by_id(int(value))
                if res:
                    choices.append(app_commands.Choice(name=res.id, value=str(res.id)))
            except ValueError:
                pass

        return choices
