from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage, ResourceMenuPageSelect, select_option

if TYPE_CHECKING:
    from apis.dnd5e.models.character_data import Background
    from apis.dnd5e.models.equipment import EquipmentCategory


@select_option(
    label="General",
    description="General {name} information.",
    value="background_general",
    page=1
)
@select_option(
    label="Personality",
    description="Starting {name} personality traits.",
    value="background_personality",
    page=2
)
@select_option(
    label="Equipment",
    description="Starting {name} equipment.",
    value="background_equipment",
    page=3
)
class BackgroundMenuPageSelect(ResourceMenuPageSelect):
    pass


class BackgroundMenuPage(ResourceMenuPage):
    resource: 'Background'

    async def generate_pages(self, interaction: Interaction) -> None:
        starting_equipment_options = []
        for equip_opt in self.resource.starting_equipment_options:
            if equip_opt.type == "equipment":
                lkp: 'EquipmentCategory'
                lkp, schema = await interaction.client.dnd_client.lookup(
                    (equip_opt.from_.equipment_category, 'equipment-categories')
                )
                starting_equipment_options.append((lkp.name, lkp.equipment))
            else:
                raise ValueError(f"Unmapped starting_equipment_options type {equip_opt.type}")

        language_options = await interaction.client.dnd_client.get_resources_for_endpoint(
            self.resource.language_options.from_.resource_list_url.split('/')[-1]
        )
        language_options = language_options.results

        # Home Page
        self.pages.append(self.embed_factory.get(
            author_name="General",
            fields=[
                (
                    f"Feature: {self.resource.feature.name}",
                    '\n\n'.join(self.resource.feature.desc),
                    False
                ),
                (
                    "Starting Proficiencies",
                    '\n'.join(f'`{p.name}`' for p in self.resource.starting_proficiencies)
                ),
                (
                    f"Languages: Choose {self.resource.language_options.choose}",
                    "\n".join(f'`{lang.name}`' for lang in language_options)
                ),
            ],
        ))

        # Personality page
        self.pages.append(self.embed_factory.get(
            author_name="Personality",
            fields=[
                (
                    f"Personality Traits: Choose {self.resource.personality_traits.choose}",
                    "\n\n".join(f"> {opt.string}" for opt in self.resource.personality_traits.from_.options),
                    False
                ),
                (
                    f"Ideals: Choose {self.resource.ideals.choose}",
                    "\n\n".join(
                        f"> {opt.desc}\nAlignments: {' '.join('`' + a.name + '`' for a in opt.alignments)}"
                        for opt in self.resource.ideals.from_.options
                    ),
                    False
                ),
                (
                    f"Bonds: Choose {self.resource.bonds.choose}",
                    "\n\n".join(f"> {opt.string}" for opt in self.resource.bonds.from_.options),
                    False
                ),
                (
                    f"Flaws: Choose {self.resource.flaws.choose}",
                    "\n\n".join(f"> {opt.string}" for opt in self.resource.flaws.from_.options),
                    False
                ),
            ]
        ))

        # Equipment page
        fields = [(
            "Starting Equipment",
            '\n'.join(f'`{e.equipment.name} x{e.quantity}`' for e in self.resource.starting_equipment),
            False
        )]
        for i, opt in enumerate(self.resource.starting_equipment_options):
            fields.append((
                f"{starting_equipment_options[i][0]}: Choose {opt.choose}",
                "\n".join(f"`{ref.name}`" for ref in starting_equipment_options[i][1])
            ))

        self.pages.append(self.embed_factory.get(
            fields=fields,
            author_name="Equipment"
        ))

        self._apply_page_numbers()


class BackgroundMenu(ResourceMenu, page_type=BackgroundMenuPage, select_type=BackgroundMenuPageSelect):
    pass
