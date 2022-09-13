from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.game_mechanics import MagicSchool


class MagicSchoolMenuPage(ResourceMenuPage):
    resource: 'MagicSchool'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            description=self.resource.desc,
        ))


class MagicSchoolMenu(ResourceMenu, page_type=MagicSchoolMenuPage):
    pass
