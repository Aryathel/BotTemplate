from typing import Any, Union

import discord

from utils import tdelta_from_str, EmbedFactory
from .bot import Bot, Interaction

debug = Bot.debug


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
    ):
        self.interaction = interaction
        self.msg = msg
        self.user = user

    async def get_response(self) -> bool:
        view = ConfirmationButtons(user=self.user)
        if type(self.msg) == discord.Embed:
            await self.interaction.response.send_message(
                embed=self.msg,
                view=view
            )
        else:
            await self.interaction.response.send_message(
                self.msg,
                view=view
            )
        await view.wait()
        return view.result


# ---------- Ban Form ----------
class BanForm(discord.ui.Modal):
    """ A modal form that appears when banning a user via context menu.

    This is an alternative to the `/ban` command, and may or may not be implemented.
    """
    bot: Bot

    def __init__(self, user: discord.Member, bot: Bot):
        self.user = user
        self.bot = bot
        self.title = f'Banning \'{user.name}\''
        super().__init__()

    duration = discord.ui.TextInput(
        label='Duration (Optional)',
        placeholder='Length of time, like "3h4m" or "2w" or other such formats.',
        required=False
    )

    reason = discord.ui.TextInput(
        label='Reason (Optional)',
        placeholder='The reason for banning the user.',
        required=False,
        style=discord.TextStyle.long,
        max_length=1000
    )

    async def on_submit(self, interaction: Interaction):
        # await self.user.ban(reason=self.reason.value)

        emb = self.bot.embeds.get(
            title=f'Banned {self.user}',
            thumbnail=self.user.display_avatar.url,
            fields=[
                {
                    "name": "Reason",
                    "value": self.reason.value,
                    "inline": False
                }
            ]
        )

        if self.duration.value:
            try:
                now = interaction.created_at
                td = tdelta_from_str(self.duration.value)
                unban_date = now + td

                emb.add_field(
                    name="Unbanned",
                    value=discord.utils.format_dt(unban_date, 'R')
                )
            except ValueError as e:
                td = None
        else:
            td = None

        await self.bot.db.bans.insert(
            user=self.user,
            guild=interaction.guild,
            banner=interaction.user,
            duration=td,
            reason=self.reason.value
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)
