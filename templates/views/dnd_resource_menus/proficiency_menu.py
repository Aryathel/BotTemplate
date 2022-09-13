from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.character_data import Proficiency


class ProficiencyMenuPage(ResourceMenuPage):
    resource: 'Proficiency'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Type', f'`{self.resource.type}`', False),
        ]
        if self.resource.classes:
            fields.append(('Classes', '\n'.join(f'`{c.name}`' for c in self.resource.classes)))
        if self.resource.races:
            fields.append(('Races', '\n'.join(f'`{r.name}`' for r in self.resource.races)))
        fields.append(('Referenced', f'`{self.resource.reference.name}`', False))
        self.pages.append(self.embed_factory.get(
            fields=fields
        ))


class ProficiencyMenu(ResourceMenu, page_type=ProficiencyMenuPage):
    pass
