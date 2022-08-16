from typing import TYPE_CHECKING, Any

import discord

from utils import Menu, MenuPage, EmbedFactory

from ...bot import Interaction

if TYPE_CHECKING:
    from apis.dnd5e.models.class_ import Class


class CLassMenuPageSelect(discord.ui.Select['DnDClassMenu']):
    def __init__(self, class_: 'Class') -> None:
        super().__init__(row=0, placeholder='Page Selection')
        self.class_ = class_

        self._populate()

    def _populate(self) -> None:
        self.add_option(
            label="General",
            description=f"General {self.class_.name} class information.",
            value="1"
        )
        self.add_option(
            label="Proficiencies",
            description=f"{self.class_.name} starting and optional proficiencies.",
            value="2"
        )
        self.add_option(
            label="Equipment",
            description=f"{self.class_.name} starting and option equipment.",
            value="3"
        )

    async def callback(self, interaction: Interaction) -> None:
        await self.view.set_page(int(self.values[0]), interaction)


class ClassMenuPage(MenuPage):
    index: int
    pages: list[discord.Embed]

    def __init__(
            self,
            class_: 'Class',
            embed_factory: EmbedFactory,
    ) -> None:
        self.class_ = class_
        self.embed_factory = embed_factory.copy().update(title=self.class_.name, url=self.class_.full_url)

    async def _generate_pages(self) -> None:
        self.pages = []
        self.pages.append(self.embed_factory.get(
            author_name="General",
            fields=[
                ("Hit Die", f"`d{self.class_.hit_die}`"),
                ("Saving Throws", '\n'.join(f'`{t.name}`' for t in self.class_.saving_throws))
            ]
        ))

        fields = [
            ("Starting Proficiencies", '\n'.join(f'`{p.name}`' for p in self.class_.proficiencies), False),
        ]
        for prof_choice in self.class_.proficiency_choices:
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
            ("Starting Equipment", '\n'.join(f'`{e.equipment.name} x{e.quantity}`' for e in self.class_.starting_equipment))
        ]
        for equip_choice in self.class_.starting_equipment_options:
            fields.append((
                f"Choose {equip_choice.choose}",
                (f'> {equip_choice.desc}:\n' if hasattr(equip_choice, 'desc') else '') +
                '\n'.join(f'`{opt.item.name}`' for opt in equip_choice.from_.options)
            ))
        self.pages.append(self.embed_factory.get(
            author_name="Equipment",
            fields=fields
        ))

        self._apply_page_numbers()

    def _apply_page_numbers(self) -> None:
        if self.is_paginating():
            max_pages = self.get_max_pages()
            for i, emb in enumerate(self.pages):
                emb.title += f" [{i + 1}/{max_pages}]"

    def is_paginating(self) -> bool:
        return self.get_max_pages() > 1

    def get_max_pages(self) -> int:
        return len(self.pages)

    def get_page(self, page_number: int) -> Any:
        self.index = page_number

    def format_page(self, menu: 'ClassMenu', page: Any) -> discord.Embed:
        return self.pages[self.index-1]


class ClassMenu(Menu):
    pages: ClassMenuPage

    def __init__(
            self,
            class_: 'Class',
            embed_factory: EmbedFactory,
            interaction: Interaction,
            ephemeral: bool = False
    ) -> None:
        page = ClassMenuPage(class_=class_, embed_factory=embed_factory)
        super().__init__(page=page, interaction=interaction, ephemeral=ephemeral, row=1)

        self._add_select()

    def _add_select(self) -> None:
        self.clear_items()
        self.add_item(CLassMenuPageSelect(self.pages.class_))
        self.populate()

    async def set_page(self, page_num: int, interaction: Interaction) -> None:
        self.current_page = page_num
        page = await self.pages.get_page(page_num)
        response = await self._get_formatted_page_args(page)
        self._update_buttons(page_num)
        await interaction.response.edit_message(**response, view=self)
