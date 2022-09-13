from typing import TYPE_CHECKING, Any, Optional, Type, Mapping, Union
import abc

import discord

from utils import MenuPage, Menu, EmbedFactory

from ...bot import Interaction


if TYPE_CHECKING:
    from apis.dnd5e.models.framework import ResourceModel


def select_option(label: str, description: str, value: str):
    def inner(cls):
        if not hasattr(cls, 'options') or isinstance(getattr(cls, 'options'), property):
            cls.options = []
        cls.options.append((label, description, value))
        return cls
    return inner


class ResourceMenuPageSelect(discord.ui.Select, abc.ABC):
    options: Union[list[tuple[str, str, str]], list[tuple[str, str, str, int]]]
    value_mapping: Mapping[str, int]

    def __init__(self, page: 'ResourceMenuPage') -> None:
        super().__init__(row=0, placeholder='Page Selection')
        self.resource = page.resource
        self.pages = page.included
        self.index = page.index

        if not hasattr(self, 'options') or not self.options:
            raise AttributeError("At least one option must be specified.")

        self._assign_pages()
        self._populate()

    def _assign_pages(self) -> None:
        opts = []
        self.value_mapping = {}
        for opt in reversed(self.options):
            if not len(opt) == 3:
                raise IndexError("SelectMenu options must have 3 elements.")
            label, desc, value = opt
            page = self.pages.get(label, None)
            if page:
                if hasattr(self.resource, 'name'):
                    desc = desc.format(name=self.resource.name)
                opts.append((label, desc, value, page))
                self.value_mapping[value] = page

        self.options = opts

    def _get_page_selected(self, i: int) -> bool:
        if i == self.index:
            return True

        vals = list(self.value_mapping.values())
        if i == vals[-1]:
            if self.index >= vals[-1]:
                return True
        elif i <= self.index < vals[vals.index(i) + 1]:
            return True

        return False

    def _populate(self) -> None:
        for i, opt in enumerate(self.options):
            self.add_option(
                label=opt[0],
                description=opt[1],
                value=opt[2],
                default=self._get_page_selected(opt[3]),
            )

    async def callback(self, interaction: Interaction) -> None:
        await self.view.set_page(self.value_mapping.get(self.values[0], 1), interaction)


class ResourceMenuPage(MenuPage, abc.ABC):
    index: int
    pages: list[discord.Embed]
    included: dict[str, int]

    _page_numbers_applied: bool

    def __init__(
            self,
            resource: 'ResourceModel',
            embed_factory: EmbedFactory,
    ) -> None:
        self.pages = []
        self.resource = resource
        self.embed_factory = embed_factory.copy().update(title=self.resource.name, url=self.resource.full_url)
        self._page_numbers_applied = False
        self.index = 1

    async def generate_pages(self, interaction: Interaction) -> None:
        raise NotImplementedError

    def _apply_page_numbers(self) -> None:
        if self.is_paginating() and not self._page_numbers_applied:
            max_pages = self.get_max_pages()
            for i, emb in enumerate(self.pages):
                emb.title += f" [{i+1}/{max_pages}]"
            self._page_numbers_applied = True

    def is_paginating(self) -> bool:
        return len(self.pages) > 1

    def get_max_pages(self) -> int:
        return len(self.pages)

    async def get_page(self, page_number: int) -> None:
        self.index = page_number

    async def format_page(self, menu: 'ResourceMenu', page: Any) -> discord.Embed:
        return self.pages[self.index-1]


class ResourceMenuMeta(type):
    def __new__(
            mcs, name, bases, attrs,
            page_type: Type[ResourceMenuPage],
            select_type: Optional[Type[ResourceMenuPageSelect]] = None
    ):
        if not page_type or not issubclass(page_type, ResourceMenuPage):
            raise TypeError("Invalid 'page_type' class parameter.")
        if select_type and not issubclass(select_type, ResourceMenuPageSelect):
            raise TypeError("Invalid 'select_type' class parameter.")
        attrs['page_type'] = page_type
        attrs['select_type'] = select_type

        return super().__new__(mcs, name, bases, attrs)

    def __init__(
            cls, name, bases, attrs,
            **kwargs
    ):
        super(ResourceMenuMeta, cls).__init__(name, bases, attrs)


class ResourceMenu(Menu, metaclass=ResourceMenuMeta, page_type=ResourceMenuPage, select_type=ResourceMenuPageSelect):
    pages: ResourceMenuPage
    page_type: Type[ResourceMenuPage]
    select_type: Optional[Type[ResourceMenuPageSelect]]

    def __init__(
            self,
            interaction: Interaction,
            resource: 'ResourceModel',
            embed_factory: EmbedFactory,
            ephemeral: bool = False,
    ) -> None:
        if not issubclass(self.page_type, ResourceMenuPage):
            raise AttributeError('The "pages_type" class attribute must be set to a "ResourceMenuPage" type.')
        if self.select_type and not issubclass(self.select_type, ResourceMenuPageSelect):
            raise AttributeError('The "select_type" class attribute must be set to a "ResourceMenuPageSelect" type.')
        page = self.page_type(resource=resource, embed_factory=embed_factory)
        super().__init__(
            page=page,
            interaction=interaction,
            ephemeral=ephemeral,
            delete_on_quit=False,
            delete_on_timeout=False,
            row=1
        )

    @property
    def has_select(self) -> bool:
        return self.pages.is_paginating() and self.select_type

    def _add_select(self) -> None:
        self.add_item(self.select_type(self.pages))

    async def fill(self) -> None:
        await self.pages.generate_pages(self.interaction)
        self.clear_items()
        if self.has_select:
            self._add_select()
        self.populate()
        self.pages._apply_page_numbers()

    async def set_page(self, page_num: int, interaction: Interaction) -> None:
        self.current_page = page_num
        page = await self.pages.get_page(page_num)
        response = await self._get_formatted_page_args(page)
        self._update_buttons(page_num)
        await interaction.response.edit_message(**response, view=self)

    def _update_buttons(self, page_num: int) -> None:
        super()._update_buttons(page_num)

        self.clear_items()
        if self.has_select:
            self._add_select()
        self.populate()

    async def start(self, content: Optional[str] = None) -> None:
        await self.fill()
        await super().start(content)
