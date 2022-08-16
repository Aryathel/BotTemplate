from typing import TYPE_CHECKING

import discord

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage, ResourceMenuPageSelect, select_option

if TYPE_CHECKING:
    from apis.dnd5e.models.class_ import Class


@select_option(
    label="General",
    description="General {name} class information.",
    value="class_general"
)
@select_option(
    label="Proficiencies",
    description="{name} starting and optional proficiencies.",
    value="class_proficiencies"
)
@select_option(
    label="Equipment",
    description="{name} starting and option equipment.",
    value="class_equipment"
)
@select_option(
    label="Class Info",
    description="{name} subclasses and multi-classing information.",
    value="class_classing"
)
class CLassMenuPageSelect(ResourceMenuPageSelect):
    pass


class ClassMenuPage(ResourceMenuPage):
    resource: 'Class'

    async def generate_pages(self, interaction: Interaction) -> None:
        self.pages.append(self.embed_factory.get(
            author_name="General",
            fields=[
                ("Hit Die", f"`d{self.resource.hit_die}`"),
                ("Saving Throws", '\n'.join(f'`{t.name}`' for t in self.resource.saving_throws))
            ]
        ))

        fields = [
            ("Starting Proficiencies", '\n'.join(f'`{p.name}`' for p in self.resource.proficiencies), False),
        ]
        for prof_choice in self.resource.proficiency_choices:
            fields.append((
                f"Choose {prof_choice.choose}",
                (f'> {prof_choice.desc}:\n' if hasattr(prof_choice, 'desc') else '') +
                '\n'.join(f'`{opt.item.name}`' for opt in prof_choice.from_.options)
            ))
        self.pages.append(self.embed_factory.get(
            author_name="Proficiencies",
            fields=fields
        ))

        fields = [
            ("Starting Equipment", '\n'.join(f'`{e.equipment.name} x{e.quantity}`' for e in self.resource.starting_equipment))
        ]
        for equip_choice in self.resource.starting_equipment_options:
            opts_str = f'> {equip_choice.desc}:' if hasattr(equip_choice, 'desc') else ''
            for opt in equip_choice.from_.options:
                opt_str = await discord.utils.maybe_coroutine(opt.to_str, interaction)
                opts_str += f'\n- `{opt_str}`'

            fields.append((
                f"Choose {equip_choice.choose}",
                opts_str
            ))
        self.pages.append(self.embed_factory.get(
            author_name="Equipment",
            fields=fields
        ))

        fields = [
            ("Subclasses", '\n'.join(f'`{s.name}`' for s in self.resource.subclasses)),
        ]
        if self.resource.multi_classing.prerequisites:
            fields.append((
                "Multiclassing Prerequisites",
                '\n'.join(
                    f'`{p.minimum_score} {p.ability_score.name}`' for p in self.resource.multi_classing.prerequisites
                )
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
                    value += f'> **Choose {choice.choose} {choice.desc.title()}:**\n'
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

        self._apply_page_numbers()


class ClassMenu(ResourceMenu, page_type=ClassMenuPage, select_type=CLassMenuPageSelect):
    pass
