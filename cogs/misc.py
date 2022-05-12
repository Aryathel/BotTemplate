import random

import discord
from discord import app_commands
from discord.ext import commands

from custom_types import EmojiTransform, Emoji
from templates import AryaBot, AryaCog, AryaInteraction, aryacommand
from utils import get_emoji_name


class MiscCog(AryaCog, name="miscellaneous"):
    name = "Miscellaneous"
    description = "Commands without a category."
    icon = "\N{GAME DIE}"
    slash_commands = sorted(['ping', 'flip', 'roll', 'urlshort', 'avatar', 'user', 'server', 'emoji'])
    help = "This commands can be just about anything, they just didn't really fit in anywhere else."

    # ---------- App Commands ----------
    @aryacommand(
        name="ping",
        description="Get response time for a discord message.",
        icon="\N{Table Tennis Paddle and Ball}",
        help="Uses the internal `latency` checker to determine how long it takes for an API request to be acknowledged."
    )
    async def ping_command(self, interaction: AryaInteraction) -> None:
        emb = self.bot.embeds.get(
            title='\N{Table Tennis Paddle and Ball} Pong!',
            description=f'The bot latency is `{round(self.bot.latency * 1000)} ms`.'
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @aryacommand(
        name="flip",
        description="Flips a coin to get heads or tails."
    )
    async def flip_command(self, interaction: AryaInteraction) -> None:
        val = random.choice([1, 2])
        emb = self.bot.embeds.get(
            title='Heads!' if val == 1 else 'Tails!'
        )
        await interaction.response.send_message(embed=emb)

    @aryacommand(
        name="roll",
        description="Pick a random number between two values.",
        icon="\N{GAME DIE}"
    )
    @app_commands.rename(min_val='min', max_val='max')
    @app_commands.describe(min_val='The minimum possible value.', max_val='The maximum possible value.')
    async def roll_command(self, interaction: AryaInteraction, min_val: int = 0, max_val: int = 100) -> None:
        val = random.randint(min_val, max_val)
        emb = self.bot.embeds.get(
            title=f'Roll {min_val}-{max_val}',
            description=f'`{val}`'
        )
        await interaction.response.send_message(embed=emb)

    @aryacommand(
        name='urlshort',
        description='Shortens a given URL.',
        icon='\N{LEFTWARDS ARROW WITH HOOK}',
        help='Uses [TinyUrl](https://tinyurl.com/app) to shorten a given url.'
    )
    @app_commands.describe(url='The URL to shorten.')
    async def urlshort_command(self, interaction: AryaInteraction, url: str) -> None:
        short = self.bot.url_shorter.tinyurl.short(url)

        emb = self.bot.embeds.get(
            title='Shortened URL',
            description=short
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @aryacommand(
        name='avatar',
        description='Gets a user\'s avatar image.',
        icon='\N{FRAME WITH PICTURE}'
    )
    @app_commands.describe(user='The user to get the avatar of, or leave blank for yourself.')
    async def avatar_command(self, interaction: AryaInteraction, user: discord.User = None) -> None:
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

    @aryacommand(
        name='user',
        description='Gets information about you or another user.',
        icon='\N{Adult}'
    )
    @app_commands.describe(user='The user to get information about, or leave blank for yourself.')
    async def user_command(self, interaction: AryaInteraction, user: discord.Member = None) -> None:
        if not user:
            user = interaction.user

        emb = self.bot.embeds.get(
            fields=[
                {
                    "name": "Created Account",
                    "value": discord.utils.format_dt(user.created_at, style='R'),
                    "inline": True
                },
                {
                    "name": "Joined Server",
                    "value": discord.utils.format_dt(user.joined_at, style='R'),
                    "inline": True
                }
            ],
            thumbnail=user.display_avatar.url,
            author_name=user,
            color=user.color
        )
        await interaction.response.send_message(embed=emb)

    @aryacommand(
        name='server',
        description='Shows general information about the server.',
        icon='\N{File Cabinet}'
    )
    @app_commands.guild_only()
    async def server_command(self, interaction: AryaInteraction) -> None:
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

    @aryacommand(
        name='emoji',
        description='Get information about an emoji.',
        icon='\N{THUMBS UP SIGN}'
    )
    @app_commands.describe(emoji='An emoji to get information about.')
    async def emoji_command(self, interaction: AryaInteraction,
                            emoji: app_commands.Transform[Emoji, EmojiTransform]) -> None:
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


async def setup(bot: AryaBot) -> None:
    await bot.add_cog(MiscCog(bot), guilds=[bot.GUILD])
