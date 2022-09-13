from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.character_data import Language


class LanguageMenuPage(ResourceMenuPage):
    resource: 'Language'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Type', f'`{self.resource.type.name.title()}`'),
            ('Typical Speakers', '\n'.join(f'`{p}`' for p in self.resource.typical_speakers))
        ]
        if self.resource.script:
            fields.append(('Script', f'`{self.resource.script}`'))

        self.pages.append(self.embed_factory.get(
            description=self.resource.desc,
            fields=fields
        ))


class LanguageMenu(ResourceMenu, page_type=LanguageMenuPage):
    pass
