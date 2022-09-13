from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import EquipmentPack


class EquipmentPackMenuPage(ResourceMenuPage):
    resource: 'EquipmentPack'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Category', f'`{self.resource.equipment_category.name}: {self.resource.gear_category.name}`', False),
            ('Cost', f'`{self.resource.cost.embed_format}`'),
            ('Contents', '\n'.join(f'`{c.item.name} x{c.quantity}`' for c in self.resource.contents), False),
        ]
        if self.resource.special:
            fields.append(('Special', '\n'.join(f'`{msg}`' for msg in self.resource.special)))
        if self.resource.properties:
            fields.append(('Properties', '\n'.join(f'`{p.name}`' for p in self.resource.properties)))

        self.pages.append(self.embed_factory.get(
            description='\n'.join(self.resource.desc),
            fields=fields
        ))


class EquipmentPackMenu(ResourceMenu, page_type=EquipmentPackMenuPage):
    pass
