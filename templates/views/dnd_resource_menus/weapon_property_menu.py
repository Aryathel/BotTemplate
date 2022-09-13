from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import WeaponProperty


class WeaponPropertyMenuPage(ResourceMenuPage):
    resource: 'WeaponProperty'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            description='\n\n'.join(self.resource.desc)
        ))


class WeaponPropertyMenu(ResourceMenu, page_type=WeaponPropertyMenuPage):
    pass
