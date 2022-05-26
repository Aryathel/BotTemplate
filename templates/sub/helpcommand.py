from math import ceil
from typing import Any, List, Optional, Dict, Union

import discord

from utils import EmbedFactory, Menu, MenuPage
from ..bot import Bot, Cog, Interaction
from ..commands import Command, Group


class HelpMenuSelect(discord.ui.Select['HelpMenu']):
    def __init__(self, commands: Dict[Cog, List[Command]]):
        super().__init__(
            placeholder='Select a category...',
            row=0
        )
        self.commands = commands
        self._populate()

    def _populate(self) -> None:
        self.add_option(
            label="Index",
            description="The help index that shows how to use me.",
            emoji="\N{EXCLAMATION QUESTION MARK}",
            value="_index"
        )
        for cog in self.commands.keys():
            self.add_option(
                label=cog.name,
                emoji=cog.icon,
                description=cog.description,
                value=cog.qualified_name
            )

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        if value == '_index':
            await self.view.rebind(HelpMenuIndex(interaction.client.embeds), interaction)
        else:
            for cog, commands in self.commands.items():
                if cog.qualified_name == value:
                    await self.view.rebind(
                        HelpMenuCog(
                            cog=cog,
                            commands=commands,
                            embed_factory=interaction.client.embeds,
                            in_bulk_help=True,
                            commands_per_page=5
                        ),
                        interaction
                    )


class HelpMenu(Menu):
    def __init__(self, page: MenuPage, interaction: Interaction):
        super().__init__(page=page, interaction=interaction, row=1)

    def add_modules(self, commands: Dict[Cog, List[Command]]) -> None:
        self.clear_items()
        self.add_item(HelpMenuSelect(commands=commands))
        self.populate()

    async def rebind(self, page: MenuPage, interaction: Interaction) -> None:
        self.pages = page
        self.current_page = 1

        page = await self.pages.get_page(1)
        response = await self._get_formatted_page_args(page)
        self._update_buttons(1)
        await interaction.response.edit_message(**response, view=self)


class HelpMenuCommand(MenuPage):
    index: int

    def __init__(
            self,
            command: Command,
            embed_factory: EmbedFactory
    ):
        self.command = command
        self.embeds = embed_factory

    def is_paginating(self) -> bool:
        return False

    def get_max_pages(self) -> Optional[int]:
        return None

    async def get_page(self, page_num: int) -> Any:
        self.index = page_num
        return self

    def format_page(self, menu: Menu, page: Any) -> discord.Embed:
        required_form = '<{}>'
        optional_form = '[{}]'
        params = {}
        for _, param in self.command._params.items():
            if param.required:
                params[required_form.format(
                    param._rename if param._rename not in [discord.utils.MISSING, '...', None] else param.name
                )] = param
            else:
                params[optional_form.format(
                    param._rename if param._rename not in [discord.utils.MISSING, '...', None] else param.name
                )] = param

        emb = self.embeds.get(
            title=f'{self.command.qualified_name} {" ".join(list(params.keys()))}',
            description=self.command.desc
        )
        for sig, param in params.items():
            emb.add_field(
                name=sig,
                value=param.description,
                inline=False
            )
        return emb


class HelpMenuGroup(MenuPage):
    index: int

    def __init__(
            self,
            group: Group,
            commands_per_page: int,
            embed_factory: EmbedFactory,
            in_bulk_help: bool
    ):
        self.group: Group = group
        self.commands: List[Command] = sorted(self.group.commands, key=lambda c: c.qualified_name)
        self.page_limit: int = commands_per_page
        self.in_bulk_help: bool = in_bulk_help
        self.embeds: EmbedFactory = embed_factory

    def is_paginating(self) -> bool:
        if self.in_bulk_help:
            return True
        else:
            if len(self.commands) > self.page_limit:
                return True
        return False

    def get_max_pages(self) -> Optional[int]:
        return ceil(len(self.commands) / self.page_limit)

    async def get_page(self, page_num: int) -> Any:
        self.index = page_num
        return self

    def format_page(self, menu: Menu, page: Any) -> discord.Embed:
        emb = self.embeds.get(
            title=f'{f"{self.group.icon} " if self.group.icon else ""}{" ".join(w.capitalize() for w in self.group.name.split(" "))} Commands',
            description=self.group.long_description,
            footer='Use \'/help command\' for more information on a command.'
        )

        start = (self.index - 1) * self.page_limit
        entries = self.get_command_frame(start)
        required_form = '<{}>'
        optional_form = '[{}]'
        for command in entries:
            params = []
            for _, param in command._params.items():
                if param.required:
                    params.append(required_form.format(
                        param._rename if param._rename not in [discord.utils.MISSING, '...', None] else param.name)
                    )
                else:
                    params.append(optional_form.format(
                        param._rename if param._rename not in [discord.utils.MISSING, '...', None] else param.name)
                    )

            emb.add_field(
                name=f'{command.qualified_name} {" ".join(params)}',
                value=command.desc,
                inline=False
            )

        return emb

    def get_command_frame(self, start: int) -> Optional[List[Command]]:
        if start < len(self.commands):
            end = start + self.page_limit
            return self.commands[start:end]
        else:
            return self.commands


class HelpMenuCog(MenuPage):
    index: int

    def __init__(
            self,
            cog: Cog,
            commands: List[Union[Command, Group, None]],
            commands_per_page: int,
            embed_factory: EmbedFactory,
            in_bulk_help: bool
    ):
        self.cog: Cog = cog
        self.commands: List[Command] = self.flatten(commands)
        self.page_limit: int = commands_per_page
        self.in_bulk_help: bool = in_bulk_help
        self.embeds: EmbedFactory = embed_factory

    def is_paginating(self) -> bool:
        if self.in_bulk_help:
            return True
        else:
            if len(self.commands) > self.page_limit:
                return True
        return False

    def get_max_pages(self) -> Optional[int]:
        return ceil(len(self.commands) / self.page_limit)

    async def get_page(self, page_num: int) -> Any:
        self.index = page_num
        return self

    def format_page(self, menu: Menu, page: Any) -> discord.Embed:
        emb = self.embeds.get(
            title=f'{f"{self.cog.icon} " if self.cog.icon else ""}{" ".join(w.capitalize() for w in self.cog.name.split(" "))} Commands',
            description=self.cog.long_description,
            footer='Use \'/help command\' for more information on a command.'
        )

        start = (self.index - 1) * self.page_limit
        entries = self.get_command_frame(start)
        required_form = '<{}>'
        optional_form = '[{}]'
        for command in entries:
            params = []
            for _, param in command._params.items():
                if param.required:
                    params.append(required_form.format(
                        param._rename if param._rename not in [discord.utils.MISSING, '...', None] else param.name)
                    )
                else:
                    params.append(optional_form.format(
                        param._rename if param._rename not in [discord.utils.MISSING, '...', None] else param.name)
                    )

            emb.add_field(
                name=f'{command.qualified_name} {" ".join(params)}',
                value=command.desc,
                inline=False
            )

        return emb

    def get_command_frame(self, start: int) -> Optional[List[Command]]:
        if start < len(self.commands):
            end = start + self.page_limit
            return self.commands[start:end]
        else:
            return self.commands

    @staticmethod
    def flatten(commands: List[Union[Command, Group]]) -> List[Command]:
        res = []
        for command in commands:
            if isinstance(command, Command):
                res.append(command)
            elif isinstance(command, Group):
                group_commands = []
                for sub_command in command.walk_commands():
                    if isinstance(sub_command, Command):
                        group_commands.append(sub_command)
                res += sorted(group_commands, key=lambda c: c.qualified_name)
        return res


class HelpMenuIndex(MenuPage):
    index: int

    def __init__(self, factory: EmbedFactory):
        self.embeds = factory

    def is_paginating(self) -> bool:
        return True

    def get_max_pages(self) -> Optional[int]:
        return 2

    async def get_page(self, page_num: int) -> Any:
        self.index = page_num
        return self

    def format_page(self, menu: HelpMenu, page: Any) -> Any:
        emb = self.embeds.get(
            title=f'Bot Help [{self.index}/{self.get_max_pages()}]',
            description="Hello! Welcome to the help page.\n\n"
                        "Here, you will find all of the information you need to use me to my full potential!\n\n"
                        "Use `/help [command]` to get more information about a specific command.\n"
                        "Use `/help [category]` to get more information about a category of commands.\n"
                        "Use the menu below to navigate command categories and pages.",
        )
        if self.index == 1:
            created = discord.utils.format_dt(menu.interaction.client.user.created_at, 'F')
            entries = [
                {
                    "name": "Who am I?",
                    "value": "I am a bot made by `Aryathel#0310`, using the [Discord.py](https://github.com/Rapptz/discord.py) library. "
                             "I am currently in development, but I server as a platform for all of Arya's creations on Discord. "
                             "In the past, the older versions of me have been used for programs in over 100 different servers and projects, "
                             "ranging from smaller community server for friends, to collegiate esports servers, to larger discords like "
                             "[Cooler Master](https://www.coolermaster.com/), [MSI](https://us.msi.com/), and [SpaceTime Strategies](https://www.spacetime.gg/)."
                             f" I was originally created on {created}.\n\n"
                             "Oh, and I am also open source!\nYou can find my code and use me as a bot template on [GitHub](https://github.com/Aryathel/BotTemplate).",
                    "inline": False
                },
                {
                    "name": "Who is your creator?",
                    "value": "I'll let her answer that herself.\n...\n"
                             "OH! Hi there \N{WAVING HAND SIGN}. I am [Arya](https://heroicoshm.page/), otherwise known as `Aryathel` online. "
                             "I am a 21 year old college student currently studying game design, with an emphasis in "
                             "computer science. Basically, I love programming, and I have been working hard for many years now to make it a career. "
                             "There isn't really too much to say about me other than that: I play a lot of video games like Destiny 2, Apex Legends, "
                             "osu!, Beat Saber, and more, and I write a lot of code.",
                    "inline": False
                }
            ]

            for e in entries:
                emb.add_field(**e)

        elif self.index == 2:
            entries = [
                {
                    "name": "How do you read my commands?",
                    "value": "For some, it can be complicated to read the commands in my help menu, so here is a quick explanation of what different parts mean.",
                    "inline": False
                },
                {
                    "name": "<argument>",
                    "value": "Angled brackets around an argument means that argument is __**required**__."
                },
                {
                    "name": "[argument]",
                    "value": "Square brackets around an argument means that argument is __**optional**__."
                },
                {
                    "name": "[A|B|C]",
                    "value": "Pipes separating arguments show options. In this example, the argument can be __**either A, or B, or C**__."
                },
                {
                    "name": "One last thing:",
                    "value": "When you type in these arguments yourselves, you do **not include the brackets**."
                             "The brackets only exist in the help command so that you can see the difference between argument types.",
                    "inline": False
                }
            ]

            for e in entries:
                emb.add_field(**e)

        return emb
