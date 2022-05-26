from datetime import timedelta
from typing import Union, List, Any, Type

import discord
from discord import app_commands
from discord.ext import commands

from utils import tdelta_from_str, clamp, str_from_tdelta
from templates.bot import Interaction, Cog
from templates.commands import Command, Group
from templates.types import AppCommandOptionType, COLORS, RGB_PATTERN, PERMISSION_FLAGS, U_EMOJI_PATTERN, \
    C_EMOJI_PATTERN, Emoji, Permission, USER_MENTION_PATTERN
from ..errors import TransformerError


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
    Whichever one comes first is then converted into a `custom_types.Emoji` object and passed to the function.
    """

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> Emoji:
        # Get the first instances of either a unicode or custom emoji (these will be None if not found).
        u_emoji = U_EMOJI_PATTERN.search(value)
        c_emoji = C_EMOJI_PATTERN.search(value)

        # Determine which emoji type to use.
        # If both emoji types were found, use the one which comes first.
        kind = -1
        if all([u_emoji, c_emoji]):
            kind = 0 if u_emoji.start() < c_emoji.start() else 1
        elif u_emoji is not None:
            kind = 0
        elif c_emoji is not None:
            kind = 1

        # Create the emoji objects.
        if kind == 0:
            emote = Emoji(name=u_emoji.group())
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
