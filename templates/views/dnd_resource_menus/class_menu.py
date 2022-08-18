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
    page=1
)
@select_option(
    label="Proficiencies",
    description="{name} starting and optional proficiencies.",
    value="class_proficiencies",
    page=2
)
@select_option(
    label="Equipment",
    description="{name} starting and option equipment.",
    value="class_equipment",
    page=3
)
@select_option(
    label="Class Info",
    description="{name} subclasses and multi-classing information.",
    value="class_classing",
    page=4
)
@select_option(
    label="Spellcasting",
    description="{name} spellcasting information.",
    value="class_spellcasting",
    page=5
)
class CLassMenuPageSelect(ResourceMenuPageSelect):
    pass


class ClassMenuPage(ResourceMenuPage):
    resource: 'Class'
    included: list[str]

    async def generate_pages(self, interaction: Interaction) -> None:
        self.included = ['General']
        self.pages.append(self.embed_factory.get(
            author_name="General",
            fields=[
                ("Hit Die", f"`d{self.resource.hit_die}`"),
                ("Saving Throws", '\n'.join(f'`{t.name}`' for t in self.resource.saving_throws))
            ]
        ))

        self.included.append('Proficiencies')
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

        self.included.append('Equipment')
        fields = []
        if self.resource.starting_equipment:
            fields.append((
                "Starting Equipment",
                '\n'.join(f'`{e.equipment.name} x{e.quantity}`' for e in self.resource.starting_equipment)
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

        self.included.append('Class Info')
        fields = [
            ("Subclasses", '\n'.join(f'`{s.name}`' for s in self.resource.subclasses)),
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
            self.included.append('Spellcasting')

            fields = [
                ("Spellcasting Ability", f"`{self.resource.spellcasting.spellcasting_ability.name}`"),
            ]
            for info in self.resource.spellcasting.info:
                fields.append((info.name, '\n\n'.join(info.desc)))

            print('\n'.join(str(f) for f in fields))
            self.pages.append(self.embed_factory.get(
                author_name="Spellcasting",
                fields=fields
            ))

        self._apply_page_numbers()


class ClassMenu(ResourceMenu, page_type=ClassMenuPage, select_type=CLassMenuPageSelect):
    pass
