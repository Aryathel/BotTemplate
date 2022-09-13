from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.spells import Spell


class SpellMenuPage(ResourceMenuPage):
    resource: 'Spell'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = []
        if self.resource.higher_level:
            fields.append(('Higher Level', '\n\n'.join(self.resource.higher_level), False))
        fields += [
            ('Level', f'`{self.resource.level}`'),
            ('Range', f'`{self.resource.range}`'),
            ('Ritual', f'`{self.resource.ritual}`'),
            ('Duration', f'`{self.resource.duration}`'),
            ('Concentration', f'`{self.resource.concentration}`'),
            ('Casting Time', f'`{self.resource.casting_time}`'),
            ('School', f'`{self.resource.school.name}`'),
        ]
        if self.resource.attack_type:
            fields.append(('Attack Type', f'`{self.resource.attack_type}`'))
        if self.resource.area_of_effect:
            fields.append(('Area of Effect', f'`{self.resource.area_of_effect.embed_format}`'))
        if self.resource.material:
            fields.append(('Material', f'`{self.resource.material}`'))
        if self.resource.components:
            fields.append(('Components', '\n'.join(f'`{c.name}`' for c in self.resource.components)))
        if self.resource.classes:
            fields.append(('Classes', '\n'.join(f'`{c.name}`' for c in self.resource.classes)))
        if self.resource.subclasses:
            fields.append(('Subclasses', '\n'.join(f'`{c.name}`' for c in self.resource.subclasses)))
        if self.resource.damage:
            fields.append(('Damage', self.resource.damage.embed_format))
        if self.resource.heal_at_slot_level:
            fields.append((
                'Heal at Slot Level',
                '\n'.join(
                    f'{level}: {h}' for level, h in
                    self.resource.heal_at_slot_level.items()
                )
            ))
        if self.resource.dc:
            fields.append(('DC', self.resource.dc.embed_format))

        self.pages.append(self.embed_factory.get(
            description='\n\n'.join(self.resource.desc),
            fields=fields
        ))


class SpellMenu(ResourceMenu, page_type=SpellMenuPage):
    pass
