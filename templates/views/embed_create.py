from typing import Optional, Callable, Awaitable

import discord
from discord import ui
from discord.utils import MISSING

from .modal import Modal


__all__ = [
    'CreateEmbedMessage'
]


class CreateEmbedMessage(Modal, title="Create Embed Message"):
    color: discord.Color
    channel: discord.TextChannel

    label = ui.TextInput(
        label="Title",
        placeholder="My Embed Message",
    )
    description = ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="This is an embed message."
    )
    thumbnail = ui.TextInput(
        label="Thumbnail URL",
        required=False,
        placeholder="https://cdn.discordapp.com/attachments/000/000/000.png"
    )
    footer_text = ui.TextInput(
        label="Footer Text",
        required=False,
        placeholder="Footer Text"
    )
    footer_icon_url = ui.TextInput(
        label="Footer Icon",
        required=False,
        placeholder="https://cdn.discordapp.com/attachments/000/000/000.png"
    )

    def __init__(
            self,
            callback: Optional[Callable[..., Awaitable[None]]] = None,
            *,
            color: discord.Color = None,
            channel: discord.TextChannel = None,
            title: str = MISSING,
            timeout: Optional[float] = None,
            custom_id: str = MISSING,
    ) -> None:
        super().__init__(callback, title=title, timeout=timeout, custom_id=custom_id)
        self.color = color
        self.channel = channel
