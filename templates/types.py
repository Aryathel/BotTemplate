import re
from enum import Enum, Flag, auto
import random
from typing import Optional, NamedTuple, List, Dict, Callable, TYPE_CHECKING, Union, Tuple

import discord

if TYPE_CHECKING:
    from database.models.role_reaction_messages import RoleReactionMessage


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

# Twitter Error Code Descriptions
TWITTER_HTTP_ERRORS: Dict[int, Tuple[str, str]] = {
    200: ("OK", "The request was successful"),
    304: ("Not Modified", "There was no new data to return."),
    400: ("Bad Request", "The request was invalid or cannot be otherwise served."),
    401: ("Unauthorized", "There was a problem authenticating your request."),
    403: ("Forbidden", "The request is understood, but it has been refused of access is not allowed."),
    404: ("Not Found", "The URI requested is invalid or the resource requested does not exist."),
    406: (
        "Not Acceptable",
        "Returned when an invalid format is specified in the request. Generally, refers to the client not accepting "
        "gzip encoding headers."
    ),
    410: ("Gone", "The resource is gone. Used to indicate an API endpoint that has been turned off."),
    422: ("Unprocessable Entity", "Returned when the data is unable to be processed."),
    429: (
        "Too Many Requests",
        "Returned when a request cannot be served due to the App's rate limit or Tweet cap having been exhausted."
    ),
    500: (
        "Internal Server Error",
        "Something is broken. This is usually a temporary error, and is typically limited in scope."
    ),
    502: ("Bad Gateway", "Twitter is down, or being upgraded."),
    503: ("Service Unavailable", "The Twitter servers are up, but overloaded with requests. Try again later."),
    504: (
        "Gateway Timeout",
        "The Twitter servers are up, but the request couldn't be serviced due to some failure internally."
    )
}
# Regex pattern for validating Twitter usernames
TWITTER_USER_PATTERN = re.compile(r'^[A-Za-z0-9_]{1,15}$')


# Possible field types to include for a Twitter User response in a request.
class TwitterUserField(Flag):
    id = auto()
    name = auto()
    username = auto()
    created_at = auto()
    description = auto()
    entities = auto()
    location = auto()
    pinned_tweet_id = auto()
    profile_image_url = auto()
    protected = auto()
    public_metrics = auto()
    url = auto()
    verified = auto()
    withheld = auto()

    def __iter__(self):
        values = self.__class__.__members__.values()
        for v in values:
            if v in self:
                yield v

    @property
    def query(self) -> str:
        return ','.join(f.name for f in self)


class TwitterTweetField(Flag):
    id = auto()
    text = auto()
    attachments = auto()
    author_id = auto()
    context_annotations = auto()
    conversation_id = auto()
    created_at = auto()
    entities = auto()
    geo = auto()
    in_reply_to_user_id = auto()
    lang = auto()
    non_public_metrics = auto()
    organic_metrics = auto()
    possibly_sensitive = auto()
    promoted_metrics = auto()
    public_metrics = auto()
    referenced_tweets = auto()
    reply_settings = auto()
    source = auto()
    withheld = auto()

    def __iter__(self):
        values = self.__class__.__members__.values()
        for v in values:
            if v in self:
                yield v

    @property
    def query(self) -> str:
        return ','.join(f.name for f in self)


class TwitterMediaField(Flag):
    media_key = auto()
    type = auto()
    url = auto()
    duration_ms = auto()
    height = auto()
    non_public_metrics = auto()
    organic_metrics = auto()
    preview_image_url = auto()
    promoted_metrics = auto()
    public_metrics = auto()
    width = auto()
    alt_text = auto()
    variants = auto()

    def __iter__(self):
        values = self.__class__.__members__.values()
        for v in values:
            if v in self:
                yield v

    @property
    def query(self) -> str:
        return ','.join(f.name for f in self)


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
    message = 17
    twitter_user = 18
    twitter_monitor = 19
    dnd_roll = 20
    dnd_resource = 21
    dnd_resource_lookup = 22


# ---------- Role Sort Options ----------
class RoleSortOption(Enum):
    """The sorting methods for the role list command."""
    default = 0
    member_count = 1
    name = 2


# ---------- Bulk Role Target Options ----------
class BulkRoleTargetOption(Enum):
    """The users targeted by a bulk role give/take command."""
    all_users = 0
    bots = 1
    humans = 2


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
    def is_custom(self) -> bool:
        return self.id is not None

    @property
    def is_known(self) -> bool:
        if self.is_custom:
            return self.discord_emoji is not None
        return True

    @property
    def usage_form(self) -> Union[str, discord.Emoji]:
        if self.is_custom:
            return self.discord_emoji
        return self.name

    def __str__(self):
        if self.is_custom:
            return f'<{"a" if self.animated else ""}:{self.name}:{self.id}>'
        else:
            return self.name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, o: Union[discord.Emoji, 'Emoji', str]) -> bool:
        if isinstance(o, discord.Emoji):
            if self.is_custom:
                return self.discord_emoji.id == o.id
            return False
        elif isinstance(o, Emoji):
            if o.name == self.name and o.id == self.id and o.animated == self.animated:
                return True
            return False
        elif isinstance(o, str):
            return self.name == o

        raise NotImplementedError


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


class Message:
    message: discord.Message
    role_reaction_msg: Optional['RoleReactionMessage']

    def __init__(self, message: discord.Message, rr_msg: Optional['RoleReactionMessage'] = None):
        self.message = message
        self.role_reaction_msg = rr_msg

    @property
    def is_role_reaction(self) -> bool:
        if self.role_reaction_msg:
            return True
        return False


# ---------- D&D Types ----------
# The pattern for parsing dice rolls from a string.
DICE_ROLL_PATTERN = re.compile(
    r"(?P<num_die>\d+)?d(?P<num_sides>\d+)(?:\s?kh\s?(?P<kh>\d+)|\s?kl\s?(?P<kl>\d+))?(?:\s?\+\s?(?P<add>\d+)|\s?-\s?(?P<sub>\d+))?",
    re.IGNORECASE
)


class DiceRoll:
    num_sides: int
    num_dice: int
    keep_highest: int
    keep_lowest: int
    add: int
    subtract: int

    value: int = None
    rolls: list[int] = None
    rolls_kept: Optional[list[int]] = None

    __defaults__ = [
        1,
        None,
        0,
        0,
        0,
        0,
    ]

    def __init__(
            self,
            num_sides: int,
            num_dice: int = 1,
            keep_highest: int = 0,
            keep_lowest: int = 0,
            add: int = 0,
            subtract: int = 0
    ):
        # Safety checks
        if num_sides < 2:
            raise ValueError("num_sides cannot be less than 2.")
        elif num_dice < 1:
            raise ValueError("num_dice cannot be less than 1.")

        elif keep_lowest and keep_lowest:
            raise ValueError("keep_highest and keep_lowest cannot be defined together, only one or the other.")
        elif keep_highest > num_dice or keep_highest < 0:
            raise ValueError("keep_highest must be between 0 and the number of dice rolled.")
        elif keep_lowest > num_dice or keep_lowest < 0:
            raise ValueError("keep_lowest must be between 0 and the number of dice rolled.")

        self.num_sides = num_sides
        self.num_dice = num_dice

        self.keep_highest = keep_highest
        self.keep_lowest = keep_lowest

        self.add = add
        self.subtract = subtract

    def __str__(self) -> str:
        return f'<DiceRoll value={self.value} query="{self.query}" rolls={self.rolls}>'

    def __repr__(self) -> str:
        return self.__str__()

    def roll(self) -> None:
        self.value, self.rolls, self.rolls_kept = self._roll()

    def _roll(self) -> Tuple[int, list[int], list[int]]:
        # Roll all of the dice.
        rolls = sorted([random.randint(1, self.num_sides) for i in range(self.num_dice)])

        # Handle keeping the highest/lowest rolls.
        rolls_kept = None
        if self.keep_highest:
            rolls_kept = rolls[-self.keep_highest:]
        elif self.keep_lowest:
            rolls_kept = rolls[:self.keep_lowest]

        # Get a preliminary total from the rolls.
        if rolls_kept:
            sub_total = sum(rolls_kept)
        else:
            sub_total = sum(rolls)

        # Handle adding/subtracting remaining constants
        total = sub_total
        if self.add:
            total += self.add
        if self.subtract:
            total -= self.subtract

        return total, rolls, rolls_kept

    @property
    def query(self) -> str:
        res = f"{self.num_dice}d{self.num_sides}"
        if self.keep_highest:
            res += f' kh{self.keep_highest}'
        elif self.keep_lowest:
            res += f' kl{self.keep_lowest}'
        if self.add:
            res += f' +{self.add}'
        if self.subtract:
            res += f' -{self.subtract}'
        return res

    @classmethod
    def from_query(cls, query: str) -> Union[list['DiceRoll'], 'DiceRoll']:
        matches = DICE_ROLL_PATTERN.findall(query)
        rolls = []
        for roll in matches:
            roll = list(roll)
            try:
                for i, v in enumerate(roll):
                    if not v:
                        roll[i] = cls.__defaults__[i]
                    else:
                        roll[i] = int(v)
            except ValueError:
                raise ValueError("Not all matched values are integers.")

            dice_roll = DiceRoll(
                num_sides=roll[1],
                num_dice=roll[0],
                keep_highest=roll[2],
                keep_lowest=roll[3],
                add=roll[4],
                subtract=roll[5]
            )
            rolls.append(dice_roll)

        if len(rolls) == 1:
            return rolls[0]
        return rolls
