from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import Weapon


class WeaponMenuPage(ResourceMenuPage):
    resource: 'Weapon'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Category', f'`{self.resource.equipment_category.name}: {self.resource.category_range}`', False),
            ('Cost', f'`{self.resource.cost.embed_format}`'),
            ('Weight', f'`{self.resource.weight}`'),
            ('Range', self.resource.range.embed_format),
        ]
        if self.resource.damage:
            fields.append(('Damage', f'`{self.resource.damage.embed_format}`'))
        if self.resource.two_handed_damage:
            fields.append(('Two-Handed Damage', f'`{self.resource.two_handed_damage.embed_format}`'))
        if self.resource.throw_range:
            fields.append(('Throw Range', self.resource.throw_range.embed_format))
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


class WeaponMenu(ResourceMenu, page_type=WeaponMenuPage):
    pass
