from typing import cast

import discord
from discord import app_commands, Color

from templates import GroupCog, Interaction
from templates import decorators, transformers
from templates.views import CreateEmbedMessage
from utils import LogType


@app_commands.guild_only()
@app_commands.checks.bot_has_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
@decorators.catch_errors
class Embeds(GroupCog, group_name='embed', name='embeds'):
    description = "Commands for creating custom embed messages in a server."
    help = "These commands are for use by moderators, " \
           "and require at least `manage_messages` permissions for both the bot and the user to be activated."
    slash_commands = ['create']
    nested = True

    @decorators.command(
        name="create",
        description="Initiates the creation of a embed message.",
        icon="\N{HEAVY PLUS SIGN}"
    )
    @app_commands.describe(color="The color to use for the reaction role message.")
    async def embed_create_command(
            self,
            interaction: Interaction,
            color: app_commands.Transform[Color, transformers.ColorTransformer] = None,
            channel: discord.TextChannel = None,
    ) -> None:
        color: Color = cast(Color, color)
        await interaction.response.send_modal(CreateEmbedMessage(self._create_callback, color=color, channel=channel))

    @decorators.handle_errors
    async def _create_callback(self, modal: CreateEmbedMessage, interaction: Interaction) -> None:
        emb = interaction.client.embeds.get(
            title=modal.label.value,
            description=modal.description.value,
            thumbnail=modal.thumbnail.value,
            footer=modal.footer_text.value,
            footer_icon=modal.footer_icon_url.value,
            color=modal.color
        )
        channel = modal.channel or interaction.channel
        msg = await channel.send(embed=emb)

        emb = self.bot.embeds.get(
            description=f"[Message created.]({msg.jump_url})"
        )

        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.error_handler
    async def error_handler(self, err: Exception, *args, **kwargs) -> None:
        interaction = args[1]
        self.bot.log(error=err, log_type=LogType.error)
        if isinstance(err, discord.HTTPException):
            if "Invalid Form Body" in str(err):
                emb = self.bot.embeds.get(
                    color=discord.Color.brand_red(),
                    description="Invalid embed received. This is usually a result of a malformed image URL for the "
                                "thumbnail or footer icon fields."
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

        await interaction.response.send_message(f"A `{type(err)}` Error Occurred", ephemeral=True)
