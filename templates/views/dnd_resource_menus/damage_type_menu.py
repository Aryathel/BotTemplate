from typing import TYPE_CHECKING, Any

import discord

from utils import Menu, MenuPage, EmbedFactory
from ...bot import Interaction

if TYPE_CHECKING:
    from apis.dnd5e.models.game_mechanics import DamageType


class DamageTypeMenuPage(MenuPage):
    def __init__(self, damage_type: 'DamageType', embed_factory: EmbedFactory) -> None:
        self.damage_type = damage_type
        self.embed_factory = embed_factory

    def is_paginating(self) -> bool:
        return False

    def get_max_pages(self) -> int:
        return 1

    async def get_page(self, page_number: int) -> Any:
        return None

    async def format_page(self, menu: 'DamageTypeMenu', page: Any) -> discord.Embed:
        return self.embed_factory.get(
            title=self.damage_type.name,
            url=self.damage_type.full_url,
            description='\n\n'.join(self.damage_type.desc)
        )


class DamageTypeMenu(Menu):
    def __init__(self, damage_type: 'DamageType', embed_factory: EmbedFactory, interaction: Interaction, ephemeral: bool = False) -> None:
        page = DamageTypeMenuPage(damage_type=damage_type, embed_factory=embed_factory)
        super().__init__(page=page, interaction=interaction, ephemeral=ephemeral)
