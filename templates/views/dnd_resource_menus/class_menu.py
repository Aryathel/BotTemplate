from math import ceil
from typing import TYPE_CHECKING

import discord

from apis.dnd5e.models.general import OptionSetOptionsArray, OptionSetEquipmentCategory

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage, ResourceMenuPageSelect, select_option

if TYPE_CHECKING:
    from apis.dnd5e.models.class_ import Class


@select_option(
    label="General",
    description="General {name} class information.",
    value="class_general",
)
@select_option(
    label="Proficiencies",
    description="{name} starting and optional proficiencies.",
    value="class_proficiencies",
)
@select_option(
    label="Equipment",
    description="{name} starting and option equipment.",
    value="class_equipment",
)
@select_option(
    label="Class Info",
    description="{name} subclasses and multi-classing information.",
    value="class_classing",
)
@select_option(
    label="Spellcasting",
    description="{name} spellcasting information.",
    value="class_spellcasting",
)
@select_option(
    label="Spells",
    description="{name} spell list.",
    value="class_spells"
)
@select_option(
    label="Levels",
    description="{name} level information.",
    value="class_levels"
)
class ClassMenuPageSelect(ResourceMenuPageSelect):
    pass


class ClassMenuPage(ResourceMenuPage):
    resource: 'Class'
    included: dict[str, int]

    async def generate_pages(self, interaction: Interaction) -> None:
        page = 1
        self.included = {'General': page}
        page += 1
        self.pages.append(self.embed_factory.get(
            author_name="General",
            fields=[
                ("Hit Die", f"`d{self.resource.hit_die}`"),
                ("Saving Throws", '\n'.join(f'`{t.name}`' for t in self.resource.saving_throws))
            ]
        ))

        self.included['Proficiencies'] = page
        page += 1
        fields = [(
            "Starting Proficiencies",
            '\n'.join(f'`{p.name}`' for p in self.resource.proficiencies),
            False
        )]
        for prof_choice in self.resource.proficiency_choices:
            if isinstance(prof_choice.from_, OptionSetOptionsArray):
                opts_str = f'> {prof_choice.desc}:' if hasattr(prof_choice, 'desc') else ''
                for opt in prof_choice.from_.options:
                    opt_str = await discord.utils.maybe_coroutine(opt.to_str, interaction)
                    opts_str += f'\n- `{opt_str}`'
                fields.append((
                    f"Choose {prof_choice.choose}",
                    opts_str
                ))
            else:
                raise TypeError(f"Unhandled choice type received: {prof_choice.from_.__class__.__name__}")
        self.pages.append(self.embed_factory.get(
            author_name="Proficiencies",
            fields=fields
        ))

        self.included['Equipment'] = page
        page += 1
        fields = []
        if self.resource.starting_equipment:
            fields.append((
                "Starting Equipment",
                '\n'.join(f'`{e.equipment.name} x{e.quantity}`' for e in self.resource.starting_equipment),
                False
            ))
        for equip_choice in self.resource.starting_equipment_options:
            if isinstance(equip_choice.from_, OptionSetOptionsArray):
                opts_str = f'> {equip_choice.desc}:' if hasattr(equip_choice, 'desc') else ''
                for opt in equip_choice.from_.options:
                    opt_str = await discord.utils.maybe_coroutine(opt.to_str, interaction)
                    opts_str += f'\n- `{opt_str}`'
                fields.append((
                    f"Choose {equip_choice.choose}",
                    opts_str
                ))
            elif isinstance(equip_choice.from_, OptionSetEquipmentCategory):
                opt_str = await discord.utils.maybe_coroutine(equip_choice.to_str, interaction)
                opts_str = f'`{opt_str}`'
                fields.append((
                    f"Choose {equip_choice.choose} from {equip_choice.from_.equipment_category.name}",
                    opts_str
                ))
            else:
                raise TypeError(f"Unhandled choice type received: {equip_choice.from_.__class__.__name__}")

        self.pages.append(self.embed_factory.get(
            author_name="Equipment",
            fields=fields
        ))

        self.included['Class Info'] = page
        page += 1
        features = await self.resource.class_features_list(interaction)
        fields = [
            ("Subclasses", '\n'.join(f'`{s.name}`' for s in self.resource.subclasses)),
            ('Features', '\n'.join(f'`{f.name}`' for f in features.results))
        ]
        if self.resource.multi_classing.prerequisites:
            fields.append((
                "Multi-classing Prerequisites",
                '\n'.join(
                    f'`{p.to_str()}`' for p in self.resource.multi_classing.prerequisites
                )
            ))
        if self.resource.multi_classing.prerequisite_options:
            choice = self.resource.multi_classing.prerequisite_options
            desc = ' ' + choice.desc.replace("-", " ").title() if choice.desc else ''
            fields.append((
                "Multi-classing Prerequisite Options",
                f'> **Choose {choice.choose}{desc}:**\n' +
                '\n'.join(f'`{p.to_str(interaction)}`' for p in choice.from_.options)
            ))
        if self.resource.multi_classing.proficiencies:
            fields.append((
                "Multi-classing Proficiencies",
                '\n'.join(f'`{p.name}`' for p in self.resource.multi_classing.proficiencies)
            ))
        if self.resource.multi_classing.proficiency_choices:
            value = ''
            for choice in self.resource.multi_classing.proficiency_choices:
                if value:
                    value += '\n'
                if choice.desc:
                    value += f'> **Choose {choice.choose} {choice.desc.title().replace("-", " ")}:**\n'
                else:
                    value += f'> **Choose {choice.choose}:**\n'
                value += ', '.join(f'`{ch.item.name}`' for ch in choice.from_.options)
            fields.append((
                "Multi-classing Proficiency Options",
                value
            ))

        self.pages.append(self.embed_factory.get(
            author_name="Class Info",
            fields=fields
        ))

        if self.resource.spellcasting:
            self.included['Spellcasting'] = page

            fields = [
                ("Spellcasting Unlock Level", f"`{self.resource.spellcasting.level}`"),
                ("Spellcasting Ability", f"`{self.resource.spellcasting.spellcasting_ability.name}`"),
            ]
            embeds = []
            for info in self.resource.spellcasting.info:
                embeds.append((info.name, '\n\n'.join(info.desc)))

            if not embeds:
                self.pages.append(self.embed_factory.get(
                    author_name="Spellcasting",
                    fields=fields
                ))
                page += 1
            else:
                for i, emb in enumerate(embeds):
                    self.pages.append(self.embed_factory.get(
                        author_name=f"Spellcasting [{i+1}/{len(embeds)}]",
                        fields=fields,
                        description=f"**{emb[0]}**\n\n{emb[1]}"
                    ))
                    page += 1

        if self.resource.spells:
            self.included['Spells'] = page
            page += 1
            spell_list = await self.resource.spells_by_level(interaction)
            fields = []
            for level, spells in spell_list.items():
                if spells:
                    fields.append((
                        f"Level {level} Spells",
                        '\n'.join(f'`{s.name}`' for s in spells)
                    ))

            self.pages.append(self.embed_factory.get(
                author_name="Spells",
                fields=fields
            ))

        self.included['Levels'] = page

        for level in await self.resource.class_levels_list(interaction):
            page += 1
            fields = [
                ("Total Ability Score Bonuses", f"`{level.ability_score_bonuses}`"),
                ("Proficiency Bonus", f"`{level.prof_bonus}`"),
            ]
            if level.features:
                fields.append(("Features Gained", '\n'.join(f'`{f.name}`' for f in level.features), False))
            if level.spellcasting:
                fields.append(("Spellcasting", level.spellcasting.embed_format, False))
            if level.class_specific:
                fields.append(("Class Specific", level.class_specific.embed_format, False))

            self.pages.append(self.embed_factory.get(
                author_name=f"Level {level.level}",
                fields=fields
            ))

        self._apply_page_numbers()


class ClassMenu(ResourceMenu, page_type=ClassMenuPage, select_type=ClassMenuPageSelect):
    pass
