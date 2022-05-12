from typing import TypeVar, Any, Optional, Dict

import discord

MenuType = TypeVar('MenuType', bound='Menu')


class MenuPage:
    def is_paginating(self) -> bool:
        raise NotImplementedError

    def get_max_pages(self) -> Optional[int]:
        return None

    async def get_page(self, page_number: int) -> Any:
        raise NotImplementedError

    async def format_page(self, menu: MenuType, page: Any) -> Any:
        raise NotImplementedError


class MenuCategory:
    page_count: int
    current_page: int
    pages: Any


class Menu(discord.ui.View):
    def __init__(
            self,
            page: MenuPage,
            interaction: discord.Interaction,
            row: int = 0
    ):
        super().__init__()

        self.pages: MenuPage = page
        self.interaction: discord.Interaction = interaction
        self.current_page: int = 1
        self.row: int = row
        self.message: Optional[discord.Message] = None

        self.clear_items()
        self.populate()

    async def _get_formatted_page_args(self, page: int) -> Dict[str, Any]:
        res = await discord.utils.maybe_coroutine(self.pages.format_page, self, page)
        if isinstance(res, dict):
            return res
        elif isinstance(res, str):
            return {'content': res, 'embed': None}
        elif isinstance(res, discord.Embed):
            return {'content': None, 'embed': res}
        else:
            return {}

    def _update_buttons(self, page_num: int) -> None:
        max_pages = self.pages.get_max_pages()

        if self.pages.is_paginating():
            self.go_first.disabled = page_num == 1
            self.go_back.disabled = page_num == 1
            self.go_next.disabled = page_num + 1 > max_pages
            self.go_last.disabled = page_num + 1 > max_pages

    def populate(self) -> None:
        self.go_first.row = self.row
        self.go_back.row = self.row
        self.go_next.row = self.row
        self.go_last.row = self.row
        self.quit.row = self.row

        if self.pages.is_paginating():
            max_pages = self.pages.get_max_pages()
            if max_pages is not None:
                self.add_item(self.go_first)
                self.add_item(self.go_back)
                self.add_item(self.go_next)
                self.add_item(self.go_last)
                self.add_item(self.quit)

    async def show_page(self, interaction: discord.Interaction, page_num: int) -> None:
        page = await self.pages.get_page(page_num)
        self.current_page = page_num

        self._update_buttons(page_num)

        response = await self._get_formatted_page_args(page)
        if response:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**response, view=self)
            else:
                await interaction.response.edit_message(**response, view=self)

    async def show_page_safe(self, interaction: discord.Interaction, page_num: int) -> None:
        max_pages = self.pages.get_max_pages()
        try:
            if max_pages is None:
                await self.show_page(interaction, page_num)
            elif max_pages >= page_num >= 1:
                await self.show_page(interaction, page_num)
        except IndexError:
            await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.interaction.user.id:
            return True
        await interaction.response.send_message('Sorry, you cannot control this menu!', ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        if self.interaction:
            await self.interaction.edit_original_message(view=None)

    async def start(self, content: Optional[str] = None) -> None:
        if not self.interaction.channel.permissions_for(self.interaction.guild.me).embed_links:
            await self.interaction.response.send_message('I cannot send embedded messages here!', ephemeral=True)
            return

        page = await self.pages.get_page(1)
        response = await self._get_formatted_page_args(page)
        if content:
            response.setdefault('content', content)

        self._update_buttons(1)
        await self.interaction.response.send_message(**response, view=self)

    @discord.ui.button(label='⋘', style=discord.ButtonStyle.grey)
    async def go_first(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.show_page(interaction, 1)

    @discord.ui.button(label='Back', style=discord.ButtonStyle.blurple)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.show_page_safe(interaction, self.current_page - 1)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def go_next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.show_page_safe(interaction, self.current_page + 1)

    @discord.ui.button(label='⋙', style=discord.ButtonStyle.grey)
    async def go_last(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.show_page(interaction, self.pages.get_max_pages())

    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.button) -> None:
        await interaction.response.defer()
        await interaction.delete_original_message()
        self.stop()
