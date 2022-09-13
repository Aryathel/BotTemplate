from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import EquipmentCategory


class EquipmentCategoryMenuPage(ResourceMenuPage):
    resource: 'EquipmentCategory'

    async def generate_pages(self, interaction: Interaction) -> None:
        page_size = 20

        equipment = self.resource.equipment.copy()

        while len(equipment) > 0:
            subset = equipment[:page_size]
            del equipment[:page_size]

            self.pages.append(self.embed_factory.get(
                fields=[
                    ('Equipment', '\n'.join(f'`{e.name}`' for e in subset))
                ]
            ))

        self._apply_page_numbers()


class EquipmentCategoryMenu(ResourceMenu, page_type=EquipmentCategoryMenuPage):
    pass
