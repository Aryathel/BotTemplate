import re
from enum import Enum
from typing import TypedDict, Optional, NamedTuple, Union, List, Dict, Callable
from datetime import timedelta

import discord
import emoji
from discord import app_commands
from discord.ext import commands
import pytimeparse


# ---------- Enums ----------
class EmbedField(TypedDict):
    """Represents the typing for an embed field.

    This is not the same as a standard Discord embed field structure, it is used for typing in the
    `utils.embeds.EmbedFactory` module for customizing visuals of an embed field.
    """
    name: str
    value: str
    inline: Optional[bool]
    value_line: Optional[bool]


# ---------- Command Options ----------
class AryaAppCommandOptionType(Enum):
    """Enum for custom command option types."""
    emoji = 12
    command = 13
    time_duration = 14
    permission = 15
    color = 16


# ---------- Color Argument ----------
COLORS: Dict[str, Callable[[], discord.Color]] = {
    "Blue": discord.Color.blue,
    "Blurple": discord.Color.blurple,
    "Brand Green": discord.Color.brand_green,
    "Brand Red": discord.Color.brand_red,
    "Dark Blue": discord.Color.dark_blue,
    "Dark Gold": discord.Color.dark_gold,
    "Dark Green": discord.Color.dark_green,
    "Dark Grey": discord.Color.dark_grey,
    "Dark Magenta": discord.Color.dark_magenta,
    "Dark Orange": discord.Color.dark_orange,
    "Dark Purple": discord.Color.dark_purple,
    "Dark Red": discord.Color.dark_red,
    "Dark Teal": discord.Color.dark_teal,
    "Dark Theme": discord.Color.dark_theme,
    "Darker Grey": discord.Color.darker_grey,
    "Default": discord.Color.default,
    "Fuchsia": discord.Color.fuchsia,
    "Gold": discord.Color.gold,
    "Green": discord.Color.green,
    "Greyple": discord.Color.greyple,
    "Light Grey": discord.Color.light_grey,
    "Lighter Grey": discord.Color.lighter_grey,
    "Magenta": discord.Color.magenta,
    "OG Blurple": discord.Color.og_blurple,
    "Orange": discord.Color.orange,
    "Purple": discord.Color.purple,
    "Random": discord.Color.random,
    "Red": discord.Color.red,
    "Yellow": discord.Color.yellow
}
RGB_PATTERN = re.compile(r'(?P<r>[0-5]{1,3}),[ ]*(?P<g>[0-5]{1,3}),[ ]*(?P<b>[0-5]{1,3})')


def clamp(num: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    return min(max(num, min_val), max_val)


class ColorTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> discord.Color:
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
                raise app_commands.TransformerError(
                    value=value,
                    opt_type=AryaAppCommandOptionType.color,  # type: ignore
                    transformer=ColorTransformer
                )

    @classmethod
    async def autocomplete(
        cls, interaction: discord.Interaction, value: str
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
PERMISSION_GROUPS: Dict[str, discord.Permissions] = {
    'Advanced': discord.Permissions.advanced(),
    'All': discord.Permissions.all(),
    'All Channel': discord.Permissions.all_channel(),
    'Elevated': discord.Permissions.elevated(),
    'General': discord.Permissions.general(),
    'Members': discord.Permissions.membership(),
    'Stage': discord.Permissions.stage(),
    'Stage Moderation': discord.Permissions.stage_moderator(),
    'Text': discord.Permissions.text(),
    'Voice': discord.Permissions.voice()
}

PERMISSION_FLAGS: List[str] = list(PERMISSION_GROUPS.keys()) + sorted(discord.Permissions.VALID_FLAGS)


class Permission(NamedTuple):
    flag: str

    @property
    def permissions(self) -> List[str]:
        res = []
        if self.flag in PERMISSION_GROUPS:
            perms = PERMISSION_GROUPS[self.flag]
            for flag in discord.Permissions.VALID_FLAGS:
                if getattr(perms, flag):
                    res.append(flag)
        else:
            res.append(self.flag)

        return res


class PermissionTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> Permission:
        if value in PERMISSION_FLAGS:
            return Permission(flag=value)

        # If no permissions were found for the argument, raise an error.
        raise discord.app_commands.TransformerError(
            value=value,
            opt_type=AryaAppCommandOptionType.permission,  # type: ignore
            transformer=PermissionTransformer
        )

    @classmethod
    async def autocomplete(
        cls, interaction: discord.Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        vals = []
        for opt in PERMISSION_FLAGS:
            if value.lower() in opt.lower() or value in [None, '']:
                vals.append(app_commands.Choice(name=opt, value=opt))
                if len(vals) >= 25:
                    break
        return vals


# ---------- Command Argument ----------
class CommandOrGroupOrCog(NamedTuple):
    object: Union[app_commands.Command, app_commands.Group, commands.Cog]


class CommandTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> CommandOrGroupOrCog:
        bot: commands.Bot = interaction.client

        for opt, obj in bot.command_autocomplete_list.items():
            if value.lower() == opt.lower():
                return CommandOrGroupOrCog(object=obj)
            elif isinstance(obj, commands.Cog) and value.lower() == obj.name.lower():
                return CommandOrGroupOrCog(object=obj)

        # If no commands were found for the argument, raise an error.
        raise discord.app_commands.TransformerError(
            value=value,
            opt_type=AryaAppCommandOptionType.command,  # type: ignore
            transformer=CommandTransformer
        )

    @classmethod
    async def autocomplete(
            cls,
            interaction: discord.Interaction,
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
def tdelta_from_str(inp: str) -> timedelta:
    seconds = pytimeparse.parse(inp)
    return timedelta(seconds=seconds)


class TimeDuration(NamedTuple):
    duration: timedelta


class TimeDurationTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> TimeDuration:
        bot: commands.Bot = interaction.client

        try:
            duration = tdelta_from_str(value)
            return TimeDuration(duration=duration)
        except Exception:
            pass

        # If no duration could be read from the input.
        raise discord.app_commands.TransformerError(
            value=value,
            opt_type=AryaAppCommandOptionType.time_duration,  # type: ignore
            transformer=TimeDurationTransformer
        )

    @classmethod
    async def autocomplete(
        cls, interaction: discord.Interaction, value: str
    ) -> List[app_commands.Choice[str]]:
        try:
            duration = tdelta_from_str(value)
            str_form = str(duration).split(' ')
            if len(str_form) > 2:
                res = ' '.join(str_form[:2])
            else:
                res = ''

            hours, minutes, seconds = str_form[-1].split(':')
            hours = int(hours)
            minutes = int(minutes)
            seconds = float(seconds)
            if hours > 0:
                res += f'{" " if not res == "" else ""}{hours} Hours'
            if minutes > 0:
                res += f'{", " if not res == "" else ""}{minutes} Minutes'
            if seconds > 0:
                res += f'{", " if not res == "" else ""}{seconds} Seconds'

            return [app_commands.Choice(name=res, value=res)]

        except Exception:
            return [app_commands.Choice(name='Invalid Format', value='Invalid Format')]


# ---------- Emoji Argument ----------
# Regex patterns for detecting unicode emojis and discord emojis in a string.
U_EMOJI_PATTERN = emoji.get_emoji_regexp()
C_EMOJI_PATTERN = re.compile(r'<:(?P<name>\w+):(?P<id>\d+)>|<a:(?P<a_name>\w+):(?P<a_id>\d+)>')


class Emoji(NamedTuple):
    """Represents an emoji found from a string.

     If this is a unicode emoji, only the `name` field will have a value, and it will be set to the unicode emoji str.

     If this is a discord emoji, the name and id will have values, as well as the animated option.
    """
    name: Optional[str]
    id: Optional[int] = None
    animated: Optional[bool] = None
    discord_emoji: Optional[discord.Emoji] = None

    @property
    def is_custom(self):
        return self.id is not None

    @property
    def is_known(self):
        return self.discord_emoji is not None

    def __str__(self):
        if self.is_custom:
            return f'<{"a" if self.animated else ""}:{self.name}:{self.id}>'
        else:
            return self.name

    def __repr__(self):
        return self.__str__()


class EmojiTransform(discord.app_commands.Transformer):
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
            raise discord.app_commands.TransformerError(
                value=value,
                opt_type=AryaAppCommandOptionType.emoji,  # type: ignore
                transformer=EmojiTransform
            )

        return emote
