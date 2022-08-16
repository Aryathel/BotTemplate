from typing import TYPE_CHECKING

import discord

from utils import Menu, MenuPage, EmbedFactory

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.character_data import Alignment


class AlignmentMenuPage(ResourceMenuPage):
    resource: 'Alignment'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            description=self.resource.desc,
            fields=[
                {
                    "name": "Abbreviation",
                    "value": f'`{self.resource.abbreviation}`'
                }
            ],
        ))


class AlignmentMenu(ResourceMenu, page_type=AlignmentMenuPage):
    pass
