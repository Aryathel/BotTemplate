import re
from enum import Enum
from typing import Optional, NamedTuple, List, Dict, Callable

import discord
import emoji

# ---------- Constants ----------
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
# Regex pattern for getting an RGB tuple from a string.
RGB_PATTERN = re.compile(r'(?P<r>[0-5]{1,3}),[ ]*(?P<g>[0-5]{1,3}),[ ]*(?P<b>[0-5]{1,3})')

# Flags for permission names for roles/users.
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

# Regex patterns for detecting unicode emojis and discord emojis in a string.
U_EMOJI_PATTERN = emoji.get_emoji_regexp()
C_EMOJI_PATTERN = re.compile(r'<:(?P<name>\w+):(?P<id>\d+)>|<a:(?P<a_name>\w+):(?P<a_id>\d+)>')

# Regex patterns for detecting Discord mentions.
USER_MENTION_PATTERN = re.compile(r'<@!(?P<id>\d+)>')


# ---------- Command Options ----------
class AppCommandOptionType(Enum):
    """Enum for custom command option types."""
    emoji = 12
    command = 13
    time_duration = 14
    permission = 15
    color = 16


# ---------- Types ----------
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

    @property
    def scheme(self) -> discord.Permissions:
        perms = discord.Permissions()
        for perm in self.permissions:
            setattr(perms, perm, True)
        return perms
