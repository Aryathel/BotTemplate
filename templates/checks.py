import discord
from discord import app_commands


def is_arya():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == interaction.client.OWNER_ID
    return app_commands.check(predicate)
