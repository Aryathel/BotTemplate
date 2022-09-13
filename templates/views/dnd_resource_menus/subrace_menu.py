from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.subraces import Subrace


class SubraceMenuPage(ResourceMenuPage):
    resource: 'Subrace'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Race', f'`{self.resource.race.name}`', False),
            ('Ability Bonuses', '\n'.join(f'`{a.embed_format}`' for a in self.resource.ability_bonuses)),
            ('Racial Traits', '\n'.join(f'`{t.name}`' for t in self.resource.racial_traits)),
        ]
        if self.resource.starting_proficiencies:
            fields.append(('Starting Proficiencies', '\n'.join(f'`{p.name}`' for p in self.resource.starting_proficiencies)))
        if self.resource.languages:
            fields.append(('Languages', '\n'.join(f'`{lang.name}`' for lang in self.resource.languages)))
        if self.resource.language_options:
            fields.append((
                f'Language Options: Choose {self.resource.language_options.choose}',
                self.resource.language_options.embed_format
            ))

        self.pages.append(self.embed_factory.get(
            description=self.resource.desc,
            fields=fields
        ))


class SubraceMenu(ResourceMenu, page_type=SubraceMenuPage):
    pass
