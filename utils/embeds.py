import datetime
from typing import Optional, Union, Any, TypedDict, TypeVar
from copy import deepcopy

import discord


EmbedFieldT = Union['EmbedField', tuple[str, str, bool], tuple[str, str]]


class EmbedField(TypedDict):
    """Represents the typing for an embed field.

    This is not the same as a standard Discord embed field structure, it is used for typing in the
    `utils.embeds.EmbedFactory` module for customizing visuals of an embed field.
    """
    name: str
    value: str
    inline: Optional[bool]
    value_line: Optional[bool]


class EmbedFactory:
    """A very simple factory for creating embed messages
    that can have any amount of detail filled in as default values
    if they are not given to the embed creation message.
    """
    def __init__(
            self,
            color: Optional[Union[int, discord.Color]] = None,
            title: Optional[Any] = None, url: Optional[Any] = None,
            description: Optional[Any] = None, timestamp: Optional[datetime.datetime] = None,
            author_name: Optional[Any] = None, author_url: Optional[Any] = None,
            author_icon_url: Optional[Any] = None, footer: Optional[Any] = None,
            footer_icon: Optional[Any] = None, image: Optional[Any] = None,
            thumbnail: Optional[Any] = None, fields: list[EmbedFieldT] = None
    ):
        self.color = color
        self.title = title
        self.url = url
        self.description = description
        self.timestamp = timestamp
        self.author_name = author_name
        self.author_url = author_url
        self.author_icon_url = author_icon_url
        self.footer = footer
        self.footer_icon = footer_icon
        self.image = image
        self.thumbnail = thumbnail
        self.fields = fields

    def copy(self) -> 'EmbedFactory':
        return deepcopy(self)

    def get(self, color: Optional[Union[int, discord.Color]] = None,
            title: Optional[Any] = None, url: Optional[Any] = None,
            description: Optional[Any] = None, timestamp: Optional[datetime.datetime] = None,
            author_name: Optional[Any] = None, author_url: Optional[Any] = None,
            author_icon_url: Optional[Any] = None, footer: Optional[Any] = None,
            footer_icon: Optional[Any] = None, image: Optional[Any] = None,
            thumbnail: Optional[Any] = None, fields: list[EmbedFieldT] = None) -> discord.Embed:
        embed = discord.Embed()

        # Setting the embed field values to be the given values if they exist,
        # and otherwise defaulting to the factory defaults, which may be None.
        embed.colour = color or self.color
        embed.title = title or self.title
        embed.url = url or self.url
        embed.description = description or self.description
        embed.timestamp = timestamp or self.timestamp

        embed.set_footer(
            text=footer or self.footer,
            icon_url=footer_icon or self.footer_icon
        )

        if image is not None or self.image is not None:
            embed.set_image(url=image or self.image)
        if thumbnail is not None or self.thumbnail is not None:
            embed.set_thumbnail(url=thumbnail or self.thumbnail)

        # The author section of an embed cannot be shown unless a name is present of some kind.
        if author_name is not None or self.author_name is not None:
            embed.set_author(
                name=author_name or self.author_name,
                url=author_url or self.author_url,
                icon_url=author_icon_url or self.author_icon_url
            )

        fields_ac = []
        if fields is not None:
            fields_ac = fields
        elif self.fields is not None:
            fields_ac = self.fields

        for field in fields_ac:
            if isinstance(field, dict):
                embed.add_field(
                    name=field.get('name'),
                    value=field.get('value'),
                    inline=field.get('inline', True)
                )
            elif isinstance(field, tuple):
                if len(field) < 3:
                    inline = True
                else:
                    inline = bool(field[2])
                embed.add_field(
                    name=field[0],
                    value=field[1],
                    inline=inline
                )

        return embed

    def update(
            self,
            color: Optional[Union[int, discord.Color]] = None,
            title: Optional[Any] = None, url: Optional[Any] = None,
            description: Optional[Any] = None, timestamp: Optional[datetime.datetime] = None,
            author_name: Optional[Any] = None, author_url: Optional[Any] = None,
            author_icon_url: Optional[Any] = None, footer: Optional[Any] = None,
            footer_icon: Optional[Any] = None, image: Optional[Any] = None,
            thumbnail: Optional[Any] = None, fields: list[EmbedField] = None
    ) -> 'EmbedFactory':
        self.color = color or self.color
        self.title = title or self.title
        self.url = url or self.url
        self.description = description or self.description
        self.timestamp = timestamp or self.timestamp
        self.author_name = author_name or self.author_name
        self.author_url = author_url or self.author_url
        self.author_icon_url = author_icon_url or self.author_icon_url
        self.footer = footer or self.footer
        self.footer_icon = footer_icon or self.footer_icon
        self.image = image or self.image
        self.thumbnail = thumbnail or self.thumbnail
        self.fields = fields or self.fields

        return self
