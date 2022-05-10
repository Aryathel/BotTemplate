import random

import discord
from discord import app_commands
from discord.ext import commands

from custom_types import EmojiTransform, Emoji
from main import AryaBot
from templates.checks import is_arya
from utils.general import get_emoji_name


class GeneralCog(commands.Cog, name="general"):
    def __init__(self, bot: AryaBot) -> None:
        self.bot: AryaBot = bot

    @app_commands.command(name="ping",
                          description="\N{Table Tennis Paddle and Ball} A simple check to see how well the bot is communicating with discord.")
    async def ping_command(self, interaction: discord.Interaction) -> None:
        emb = self.bot.embeds.get(
            title='\N{Table Tennis Paddle and Ball} Pong!',
            description=f'The bot latency is `{round(self.bot.latency * 1000)} ms`.'
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="flip", description="Flips a coin to get heads or tails.")
    async def flip_command(self, interaction: discord.Interaction) -> None:
        val = random.choice([1, 2])
        emb = self.bot.embeds.get(
            title='Heads!' if val == 1 else 'Tails!'
        )
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="roll", description="1\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Pick a random number between two values.")
    @app_commands.rename(min_val='min', max_val='max')
    @app_commands.describe(min_val='The minimum possible value.', max_val='The maximum possible value.')
    async def roll_command(self, interaction: discord.Interaction, min_val: int = 0, max_val: int = 100):
        val = random.randint(min_val, max_val)
        emb = self.bot.embeds.get(
            title=f'Roll {min_val}-{max_val}',
            description=f'`{val}`'
        )
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name='urlshort', description='Shortens a given URL.')
    @app_commands.describe(url='The URL to shorten.')
    async def urlshort_command(self, interaction: discord.Interaction, url: str):
        short = self.bot.url_shorter.tinyurl.short(url)

        emb = self.bot.embeds.get(
            title='Shortened URL',
            description=short
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name='avatar', description='\N{Frame with Picture} Gets a user\'s avatar image.')
    @app_commands.describe(user='The user to get the avatar of, or leave blank for yourself.')
    async def avatar_command(self, interaction: discord.Interaction, user: discord.User = None):
        if not user:
            user = interaction.user

        emb = self.bot.embeds.get(
            title='Avatar Link',
            url=user.display_avatar.url,
            image=user.display_avatar.url,
            author_name=user,
            author_icon_url=user.display_avatar.url,
            color=user.color
        )
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name='user', description='\N{Adult} Gets information about you or another user.')
    @app_commands.describe(user='The user to get information about, or leave blank for yourself.')
    async def user_command(self, interaction: discord.Interaction, user: discord.Member = None):
        if not user:
            user = interaction.user

        emb = self.bot.embeds.get(
            fields=[
                {
                    "name": "Created Account",
                    "value": '└' + discord.utils.format_dt(user.created_at, style='R'),
                    "inline": True
                },
                {
                    "name": "Joined Server",
                    "value": '└' + discord.utils.format_dt(user.joined_at, style='R'),
                    "inline": True
                }
            ],
            thumbnail=user.display_avatar.url,
            author_name=user,
            color=user.color
        )
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name='server', description='\N{File Cabinet} Shows general information about the server.')
    @app_commands.guild_only()
    async def server_command(self, interaction: discord.Interaction):
        guild = interaction.guild
        emb = self.bot.embeds.get(
            title=guild.name,
            fields=[
                {
                    "name": "ID",
                    "value": f'`{guild.id}`',
                    "inline": True
                },
                {
                    "name": "Created",
                    "value": discord.utils.format_dt(guild.created_at, style='R'),
                    "inline": True
                },
                {
                    "name": "Owned By",
                    "value": guild.owner.mention,
                    "inline": True
                },
                {
                    "name": f"Members ({guild.member_count})",
                    "value": f"`{len([m for m in guild.members if m.status is not discord.Status.offline])}` Online\n`{guild.premium_subscription_count}` Boosts",
                    "inline": True
                },
                {
                    "name": f"Channels ({len([ch for ch in guild.channels if ch.type is not discord.ChannelType.category])})",
                    "value": f"`{len([ch for ch in guild.channels if ch.type is discord.ChannelType.text])}` Text\n`{len([ch for ch in guild.channels if ch.type in [discord.ChannelType.voice, discord.ChannelType.stage_voice]])}` Voice",
                    "inline": True
                },
                {
                    "name": f"Roles ({len(guild.roles)})",
                    "value": "Use `/roles` to view.",
                    "inline": True
                }
            ],
            thumbnail=guild.icon
        )
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name='emoji', description='Get information about an emoji.')
    @app_commands.describe(emoji='An emoji to get information about.')
    async def emoji_command(self, interaction: discord.Interaction,
                            emoji: app_commands.Transform[Emoji, EmojiTransform]):
        emoji: Emoji
        if emoji.is_known:
            try:
                invite = await emoji.discord_emoji.guild.vanity_invite()
            except Exception as e:
                invite = None
            emb = self.bot.embeds.get(
                title=f'{emoji} Information',
                thumbnail=emoji.discord_emoji.url,
                fields=[
                    {
                        "name": "String Literal",
                        "value": f'`{emoji}`',
                        "inline": False
                    },
                    {
                        "name": "ID",
                        "value": f'`{emoji.id}`'
                    },
                    {
                        "name": "Name",
                        "value": f'`{emoji.name}`'
                    },
                    {
                        "name": "Guild",
                        "value": f"[`{emoji.discord_emoji.guild.name}`]({invite})" if invite else f'`{emoji.discord_emoji.guild.name}`'
                    },
                    {
                        "name": "From Twitch",
                        "value": "`Yes`" if emoji.discord_emoji.managed else "`No`"
                    },
                    {
                        "name": "Created",
                        "value": discord.utils.format_dt(emoji.discord_emoji.created_at, 'R')
                    }
                ]
            )
        elif emoji.is_custom:
            emb = self.bot.embeds.get(
                title=f'{emoji} Information',
                fields=[
                    {
                        "name": "String Literal",
                        "value": f'`{emoji}`',
                        "inline": False
                    },
                    {
                        "name": "Name",
                        "value": f'`{emoji.name}`'
                    },
                    {
                        "name": "ID",
                        "value": f'`{emoji.id}`'
                    }
                ]
            )
        else:
            val = get_emoji_name(emoji.name)
            emb = self.bot.embeds.get(
                title=f'{emoji} Information',
                fields=[
                    {
                        "name": "String Literal",
                        "value": f"`{val}`"
                    }
                ]
            )

        await interaction.response.send_message(embed=emb)

    @app_commands.command(name='sync',
                          description='\N{Envelope with Downwards Arrow Above} Syncs the slash commands to Discord.')
    @is_arya()
    async def sync_commands(self, interaction: discord.Interaction):
        await interaction.response.send_message('Commands syncing...', ephemeral=True)
        await self.bot.tree.sync(guild=self.bot.GUILD)
        print('> Synced commands to discord.')

    @sync_commands.error
    async def sync_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                'You need to be my creator to do that, and you are not. Sorry ¯\\_(ツ)_/¯', ephemeral=True)
            interaction.extras['handled'] = True


async def setup(bot: AryaBot) -> None:
    await bot.add_cog(GeneralCog(bot), guilds=[bot.GUILD])
