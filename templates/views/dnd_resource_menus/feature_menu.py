from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.features import Feature


class FeatureMenuPage(ResourceMenuPage):
    resource: 'Feature'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Level', f"`{self.resource.level}`"),
            ('Class', f"`{self.resource.class_.name}`"),
        ]
        if self.resource.subclass:
            fields.append(('Subclass', f'`{self.resource.subclass.name}`'))
        if self.resource.parent:
            fields.append(('Parent Feature', f'`{self.resource.parent.name}`'))
        if self.resource.prerequisites:
            msgs = []
            for p in self.resource.prerequisites:
                if p.type.name == 'feature':
                    interaction.client.debug(self.resource.name)
                msgs.append(await p.format(interaction))
            fields.append((
                'Prerequisites',
                '\n'.join(f'`{p}`' for p in msgs),
                False
            ))
        self.pages.append(self.embed_factory.get(
            description='\n'.join(self.resource.desc),
            fields=fields
        ))


class FeatureMenu(ResourceMenu, page_type=FeatureMenuPage):
    pass
