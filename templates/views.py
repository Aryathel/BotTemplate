import discord
from discord import app_commands

from utils.general import tdelta_from_str
from utils.embeds import EmbedFactory


class BanForm(discord.ui.Modal):
    def __init__(self, user: discord.Member, bot):
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

    async def on_submit(self, interaction: discord.Interaction):
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
            except Exception as e:
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
