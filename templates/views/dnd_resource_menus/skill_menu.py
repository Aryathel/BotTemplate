from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.character_data import Skill


class SkillMenuPage(ResourceMenuPage):
    resource: 'Skill'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            description='\n\n'.join(self.resource.desc),
            fields=[('Related Ability Score', f'`{self.resource.ability_score.name}`')]
        ))


class SkillMenu(ResourceMenu, page_type=SkillMenuPage):
    pass
