from typing import TYPE_CHECKING

import discord

from utils import Menu, MenuPage, EmbedFactory
from ...bot import Interaction

if TYPE_CHECKING:
    from apis.dnd5e.models.game_mechanics import Condition


class ConditionMenuPage(MenuPage):
    def __init__(self, condition: 'Condition', embed_factory: EmbedFactory) -> None:
        self.condition = condition
        self.embed_factory = embed_factory

    def is_paginating(self) -> bool:
        return False

    def get_max_pages(self) -> int:
        return 1

    async def get_page(self, page_number: int) -> None:
        return None

    async def format_page(self, menu: 'ConditionMenu', page: 'ConditionMenuPage') -> discord.Embed:
        return self.embed_factory.get(
            title=self.condition.name,
            url=self.condition.full_url,
            description='\n\n'.join(self.condition.desc)
        )


class ConditionMenu(Menu):
    def __init__(self, interaction: Interaction, condition: 'Condition', embed_factory: EmbedFactory, ephemeral: bool = False):
        page = ConditionMenuPage(condition, embed_factory)
        super().__init__(page=page, interaction=interaction, ephemeral=ephemeral)
