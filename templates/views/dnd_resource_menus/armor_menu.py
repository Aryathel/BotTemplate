from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import Armor


class ArmorMenuPage(ResourceMenuPage):
    resource: 'Armor'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Category', f'`{self.resource.equipment_category.name}: {self.resource.armor_category}`', False),
            ('Cost', f'`{self.resource.cost.embed_format}`'),
            ('Weight', f'`{self.resource.weight}`'),
            ('Armor Class', f'`{self.resource.armor_class.embed_format}`'),
            ('Minimum Strength Required', f'`{self.resource.str_minimum}`'),
            ('Stealth Disadvantage', f'`{self.resource.stealth_disadvantage}`'),
        ]
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


class ArmorMenu(ResourceMenu, page_type=ArmorMenuPage):
    pass
