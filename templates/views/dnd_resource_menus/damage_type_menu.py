from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.game_mechanics import DamageType


class DamageTypeMenuPage(ResourceMenuPage):
    resource: 'DamageType'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            title=self.resource.name,
            url=self.resource.full_url,
            description='\n\n'.join(self.resource.desc)
        ))


class DamageTypeMenu(ResourceMenu, page_type=DamageTypeMenuPage):
    pass
