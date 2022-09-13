from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.feats import Feat


class FeatMenuPage(ResourceMenuPage):
    resource: 'Feat'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            description='\n'.join(self.resource.desc),
            fields=[
                ('Prerequisites', '\n'.join(f'`{p.embed_format}`' for p in self.resource.prerequisites))
            ]
        ))


class FeatMenu(ResourceMenu, page_type=FeatMenuPage):
    pass
