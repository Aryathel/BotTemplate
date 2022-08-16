from typing import TYPE_CHECKING, Optional, Any

import discord

from utils import EmbedFactory
from utils.pagination import Menu, MenuPage
from utils.images import get_roll_text

from ..bot import Interaction
from ..types import DiceRoll

if TYPE_CHECKING:
    from io import BytesIO


class DiceRollMenu(Menu):
    def __init__(self, page: MenuPage, interaction: Interaction, ephemeral: bool = False):
        super().__init__(page=page, interaction=interaction, row=1, ephemeral=ephemeral)


class DiceRollPage(MenuPage):
    index: int
    image: Optional['BytesIO']
    initial: bool

    def __init__(self, rolls: list[DiceRoll], embed_factory: EmbedFactory):
        self.rolls = rolls
        self.embed_factory = embed_factory

        self.image = None
        self.initial = True

    def is_paginating(self) -> bool:
        return len(self.rolls) > 1

    def get_max_pages(self) -> int:
        return len(self.rolls)

    async def get_page(self, page_number: int) -> 'DiceRollPage':
        self.index = page_number

        return self

    def format_page(self, menu: DiceRollMenu, page: 'DiceRollPage') -> dict[str, Any]:
        total = sum(roll.value for roll in self.rolls)
        roll = self.rolls[self.index-1]

        file = None
        if self.initial:
            if not self.image:
                self.image = get_roll_text(total)
                self.image.seek(0)

            file = discord.File(self.image, filename='image.png')
            self.initial = False

        fields = [{
            "name": f"d{roll.num_sides} Rolls",
            "value": f"`{', '.join(str(r) for r in roll.rolls)}`"
        }]

        if roll.keep_lowest or roll.keep_highest:
            fields.append({
                "name": f"{'Highest' if roll.keep_highest else 'Lowest'}  {roll.keep_highest or roll.keep_lowest} d{roll.num_sides} Rolls",
                "value": f"`{', '.join(str(r) for r in roll.rolls_kept)}`"
            })

        emb = self.embed_factory.get(
            title=f"Total: {total}",
            description='\n'.join(
                f"`{r.query}` = `{r.value}`"
                for r in self.rolls
            ),
            thumbnail="attachment://image.png",
            fields=fields
        )
        if self.is_paginating():
            emb.title += f' [{self.index}/{self.get_max_pages()}]'

        res = {'embed': emb}
        if file:
            res['file'] = file

        return res
