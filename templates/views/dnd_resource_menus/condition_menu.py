from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.game_mechanics import Condition


class ConditionMenuPage(ResourceMenuPage):
    resource: 'Condition'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            title=self.resource.name,
            url=self.resource.full_url,
            description='\n\n'.join(self.resource.desc)
        ))


class ConditionMenu(ResourceMenu, page_type=ConditionMenuPage):
    pass
