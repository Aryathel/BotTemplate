from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage, ResourceMenuPageSelect, select_option

if TYPE_CHECKING:
    from apis.dnd5e.models.subclasses import Subclass


@select_option(
    label='General',
    description='{name} general information.',
    value='subclass_general'
)
@select_option(
    label='Spells',
    description='{name} spell list.',
    value='subclass_spells'
)
@select_option(
    label='Levels',
    description='{name} level information.',
    value='subclass_levels'
)
class SubclassMenuPageSelect(ResourceMenuPageSelect):
    pass


class SubclassMenuPage(ResourceMenuPage):
    resource: 'Subclass'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.included = {'General': 1}

        fields = []
        features = await self.resource.subclass_features_list(interaction)
        fields.append(('Features', '\n'.join(f'`{f.name}`' for f in features.results)))

        self.pages.append(self.embed_factory.get(
            author_name='General',
            description=f'**{self.resource.subclass_flavor}**\n' + '\n\n'.join(self.resource.desc),
            fields=fields
        ))

        page = 2
        if self.resource.spells:
            spell_batches = [[self.resource.spells[0].embed_format]]
            for spell in self.resource.spells[1:]:
                if len('\n'.join(spell_batches[-1] + [spell.embed_format])) > 1024:
                    spell_batches.append([spell.embed_format])
                else:
                    spell_batches[-1].append(spell.embed_format)

            fields = [('Spells', '\n'.join(spell_batches[0]))]
            for batch in spell_batches[1:]:
                fields.append(('Spells (cont.)', '\n'.join(batch)))

            self.included['Spells'] = 2
            page += 1
            self.pages.append(self.embed_factory.get(
                author_name='Spells',
                fields=fields
            ))

        self.included['Levels'] = page

        levels = await self.resource.subclass_levels_list(interaction)
        for level in levels:
            fields = [
                ('Class', f'`{level.class_.name}`'),
                ('Subclass', f'`{level.subclass.name}`'),
            ]
            if level.features:
                fields.append(('Features', '\n'.join(f'`{f.name}`' for f in level.features)))
            if level.spellcasting:
                fields.append(('Spellcasting', level.spellcasting.embed_format, False))
            if level.subclass_specific:
                fields.append(('Subclass Specific', level.subclass_specific.embed_format, False))

            self.pages.append(self.embed_factory.get(
                author_name=f'Level {level.level}',
                fields=fields
            ))


class SubclassMenu(ResourceMenu, page_type=SubclassMenuPage, select_type=SubclassMenuPageSelect):
    pass
