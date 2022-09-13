from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import Vehicle


class VehicleMenuPage(ResourceMenuPage):
    resource: 'Vehicle'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Category', f'`{self.resource.equipment_category.name}: {self.resource.vehicle_category}`', False),
            ('Cost', f'`{self.resource.cost.embed_format}`'),
        ]
        if self.resource.speed:
            fields.append(('Speed', f'`{self.resource.speed.embed_format}`'))
        if self.resource.capacity:
            fields.append(('Capacity', f'`{self.resource.capacity}`'))
        if self.resource.weight:
            fields.append(('Weight', f'`{self.resource.weight}`'))
        if self.resource.special:
            fields.append(('Special', '\n'.join(f'`{msg}`' for msg in self.resource.special)))
        if self.resource.contents:
            fields.append(('Contents', '\n'.join(f'`{c.item.name} x{c.quantity}`' for c in self.resource.contents)))
        if self.resource.properties:
            fields.append(('Properties', '\n'.join(f'`{p.name}`' for p in self.resource.properties)))

        self.pages.append(self.embed_factory.get(
            description='\n'.join(self.resource.desc),
            fields=fields
        ))


class VehicleMenu(ResourceMenu, page_type=VehicleMenuPage):
    pass
