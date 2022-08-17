from typing import Optional, Callable, Awaitable

from discord.ui import Modal as DiscordModal
from discord.utils import MISSING

from ..bot import Interaction


class Modal(DiscordModal):
    callback: Optional[Callable[..., Awaitable[None]]]

    def __init__(
            self,
            callback: Optional[Callable[..., Awaitable[None]]] = None,
            *,
            title: str = MISSING,
            timeout: Optional[float] = None,
            custom_id: str = MISSING,
    ) -> None:
        self.callback = callback
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    async def on_submit(self, interaction: Interaction) -> None:
        await self.callback(self, interaction)
