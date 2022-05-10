from abc import ABC
from enum import Enum
import re
from typing import TypedDict, Optional, NamedTuple, Union

import discord
import emoji


# Regex patterns for detecting unicode emojis and discord emojis in a string.
U_EMOJI_PATTERN = emoji.get_emoji_regexp()
C_EMOJI_PATTERN = re.compile(r'<:(?P<name>\w+):(?P<id>\d+)>|<a:(?P<a_name>\w+):(?P<a_id>\d+)>')


class EmbedField(TypedDict):
    """Represents the typing for an embed field.

    This is not the same as a standard Discord embed field structure, it is used for typing in the
    `utils.embeds.EmbedFactory` module for customizing visuals of an embed field.
    """
    name: str
    value: str
    inline: Optional[bool]
    value_line: Optional[bool]


class AryaAppCommandOptionType(Enum):
    emoji = 12


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
                opt_type=AryaAppCommandOptionType.emoji,
                transformer=EmojiTransform
            )

        return emote
