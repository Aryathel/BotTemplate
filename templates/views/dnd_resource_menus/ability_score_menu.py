from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.character_data import AbilityScore


class AbilityScoreMenuPage(ResourceMenuPage):
    resource: 'AbilityScore'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            description='\n\n'.join(self.resource.desc),
            fields=[
                ('Abbreviation', f'`{self.resource.name}`', False),
                (
                    'Related Skills',
                    '\n'.join(f'`{s.name}`' for s in self.resource.skills)
                    if self.resource.skills else '`None`'
                )
            ],
        ))


class AbilityScoreMenu(ResourceMenu, page_type=AbilityScoreMenuPage):
    pass
