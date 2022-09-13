from typing import TYPE_CHECKING, Mapping

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage, ResourceMenuPageSelect, select_option

if TYPE_CHECKING:
    from apis.dnd5e.models.races import Race


@select_option(
    label='General',
    description='{name} general information.',
    value='race_general'
)
@select_option(
    label='Extra Options',
    description='{name} extra race options.',
    value='race_options'
)
class RaceMenuPageSelect(ResourceMenuPageSelect):
    pass


class RaceMenuPage(ResourceMenuPage):
    resource: 'Race'
    included: Mapping[str, int]

    async def generate_pages(self, interaction: Interaction) -> None:
        self.included = {'General': 1}
        fields = [
            ('Speed', f'`{self.resource.speed}`'),
            (f'Size', f'{self.resource.size_description}\n> `{self.resource.size}`', False),
            ('Age', f'{self.resource.age}', False),
            ('Alignment', f'{self.resource.alignment}', False),
            (
                'Languages',
                f'{self.resource.language_desc}\n' +
                '\n'.join(f'> `{lang.name}`' for lang in self.resource.languages),
                False
            ),
            ('Ability Bonuses', '\n'.join(f'`{a.embed_format}`' for a in self.resource.ability_bonuses))
        ]
        if self.resource.traits:
            fields.append(('Traits', '\n'.join(f'`{t.name}`' for t in self.resource.traits)))
        if self.resource.starting_proficiencies:
            fields.append(('Starting Proficiencies', '\n'.join(f'`{p.name}`' for p in self.resource.starting_proficiencies)))
        if self.resource.subraces:
            fields.append(('Subraces', '\n'.join(f'`{r.name}`' for r in self.resource.subraces)))

        self.pages.append(self.embed_factory.get(
            author_name='General',
            fields=fields
        ))

        fields = []
        if self.resource.ability_bonus_options:
            fields.append((
                f'Ability Bonus Options: Choose {self.resource.ability_bonus_options.choose}',
                self.resource.ability_bonus_options.embed_format,
                False
            ))
        if self.resource.starting_proficiency_options:
            fields.append((
                f'Starting Proficiency Options: Choose {self.resource.starting_proficiency_options.choose}',
                self.resource.starting_proficiency_options.embed_format,
                False
            ))
        if self.resource.language_options:
            fields.append((
                f'Language Options: Choose {self.resource.language_options.choose}',
                self.resource.language_options.embed_format,
                False
            ))

        if fields:
            self.included['Extra Options'] = 2
            self.pages.append(self.embed_factory.get(
                author_name='Extra Options',
                fields=fields
            ))


class RaceMenu(ResourceMenu, page_type=RaceMenuPage, select_type=RaceMenuPageSelect):
    pass
