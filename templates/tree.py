import discord
from discord import app_commands

from utils import LogType
from .bot import AryaBot


class AryaCommandTree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if interaction.extras.get('handled', False):
            return

        needs_syncing = (
            app_commands.CommandSignatureMismatch,
            app_commands.CommandNotFound
        )

        if isinstance(error, needs_syncing):
            await interaction.response.send_message(
                "Sorry, this command is unavailable. It likely has received an update in the backend, "
                "and needs to be re-synced.", ephemeral=True
            )
            self.client.log(
                f'Commands need to be synced. Source: "{interaction.command.name}"',
                urgent=True,
                log_type=LogType.warning
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            perms = []
            for p in error.missing_permissions:
                perms.append(f"`{' '.join(w.capitalize() for w in p.split('_'))}`")
            await interaction.response.send_message(
                f'Please give me the following permissions to use this command: {", ".join(perms)}',
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            perms = []
            for p in error.missing_permissions:
                perms.append(f"`{' '.join(w.capitalize() for w in p.split('_'))}`")
            await interaction.response.send_message(
                f'You are missing the following permissions to use this command: {", ".join(perms)}',
                ephemeral=True
            )
        elif isinstance(error, app_commands.TransformerError):
            await interaction.response.send_message(
                f'Failed to convert `{error.value}` to a `{error.type.name}`.',
                ephemeral=True
            )
        elif isinstance(error, discord.Forbidden):
            await interaction.response.send_message(
                f'I do not have permission to do that.',
                ephemeral=True
            )
        else:
            self.client.log(
                f'Unhandled "{type(error).__name__}" in "{interaction.command.name}" Command',
                log_type=LogType.error,
                error=error,
                divider=True
            )

        interaction.extras['handled'] = True


class AryaInteraction(discord.Interaction):
    client: AryaBot
