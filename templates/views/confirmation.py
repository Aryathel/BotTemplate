from typing import Union, Any

import discord

from ..bot import Interaction


# ---------- Confirmation ----------
class ConfirmationButtons(discord.ui.View):
    """A view attached to a message which asks for user confirmation."""
    user: discord.User
    result: bool = False

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji='\N{HEAVY MULTIPLICATION X}')
    async def cancel(self, interaction: Interaction, button: discord.ui.Button):
        self.result = False
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.green, emoji='\N{HEAVY CHECK MARK}')
    async def confirm(self, interaction: Interaction, button: discord.ui.Button):
        self.result = True
        await interaction.response.defer()
        self.stop()

    def __init__(
            self,
            user: discord.User,
            timeout: int = 30
    ):
        self.user = user
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not interaction.user.id == self.user.id:
            await interaction.response.send_message(f'This is not your message to interact with!', ephemeral=True)
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        self.result = False

    async def on_error(self, interaction: Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        self.result = False
        await interaction.response.defer()


class Confirmation:
    """Represents a confirmation message sent to a user."""
    interaction: Interaction
    title: str
    msg: Union[str, discord.Embed]
    user: discord.User

    def __init__(
            self,
            interaction: Interaction,
            user: discord.User,
            msg: Union[str, discord.Embed] = 'Are you sure you want to do that?',
            ephemeral: bool = False
    ):
        self.interaction = interaction
        self.msg = msg
        self.user = user
        self.ephemeral = ephemeral

    async def get_response(self) -> bool:
        view = ConfirmationButtons(user=self.user)
        if isinstance(self.msg, discord.Embed):
            await self.interaction.response.send_message(
                embed=self.msg,
                view=view,
                ephemeral=self.ephemeral
            )
        else:
            await self.interaction.response.send_message(
                self.msg,
                view=view,
                ephemeral=self.ephemeral
            )
        await view.wait()
        return view.result
