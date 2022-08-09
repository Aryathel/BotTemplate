from datetime import datetime
from typing import TYPE_CHECKING, cast, Optional
import os

import discord
from discord import app_commands
from discord.ext import tasks
import tweepy.asynchronous

from templates import Bot, GroupCog, Interaction, TwitterUserField as TUF, TwitterTweetField as TTF, \
    TwitterMediaField as TMF
from templates import decorators, transformers
from templates.errors import TwitterError
from utils import LogType, EmbedFactory
from database.models.twitter_monitors import TwitterMonitor

if TYPE_CHECKING:
    from aiohttp import ClientResponse as aiohttpResponse

user_fields = TUF.id | TUF.name | TUF.username | TUF.profile_image_url
tweet_fields = (
        TTF.id | TTF.text | TTF.attachments | TTF.author_id | TTF.created_at | TTF.in_reply_to_user_id |
        TTF.referenced_tweets | TTF.entities
)
media_fields = TMF.media_key | TMF.type | TMF.url | TMF.preview_image_url


class AsyncStreamingClient(tweepy.asynchronous.AsyncStreamingClient):
    bot: Bot
    embed_factory = EmbedFactory(
        color=discord.Color.from_str("#1DA1F2"),
        footer="Twitter",
        footer_icon="https://abs.twimg.com/favicons/twitter.2.ico",
    )

    def __init__(self, bearer_token, bot: Bot, *, return_type=tweepy.Response,
                 wait_on_rate_limit=False, **kwargs) -> None:
        super().__init__(bearer_token, return_type=return_type, wait_on_rate_limit=wait_on_rate_limit, **kwargs)
        self.bot = bot

    async def on_response(self, response: tweepy.StreamResponse) -> None:
        self.bot.log("TWITTER RESPONSE:", response, log_type=LogType.twitter)

        if response.data and isinstance(response.data, tweepy.Tweet):
            tweet = response.data

            monitors = [m for m in self.bot.twitter_monitors if m.twitter_user_id == int(tweet.author_id)]

            if monitors:
                user = await self.resolve_user(tweet.author_id)
                if user:
                    emb = self.embed_factory.get(
                        thumbnail=user.profile_image_url,
                        url=f"https://twitter.com/{user.username}/status/{tweet.id}",
                        timestamp=tweet.created_at
                    )

                    if tweet.attachments and tweet.attachments.get('media_keys'):
                        if response.includes and response.includes.get('media'):
                            media: list[tweepy.Media] = response.includes['media']
                            for m in media:
                                if m.media_key == tweet.attachments['media_keys'][0]:
                                    if m.preview_image_url:
                                        emb.set_image(url=m.preview_image_url)
                                    else:
                                        emb.set_image(url=m.url)
                        if tweet.entities and tweet.entities['urls']:
                            for url in tweet.entities['urls']:
                                if url.get('media_key', None) in tweet.attachments['media_keys']:
                                    tweet.text = tweet.text.replace(url['url'], '')

                    if tweet.referenced_tweets and response.includes:
                        if tweet.referenced_tweets[0].type == 'retweeted':
                            referenced: Optional[tweepy.Tweet] = None
                            referenced_author: Optional[tweepy.User] = None
                            for tw in response.includes['tweets']:
                                if tw.id == tweet.referenced_tweets[0].id:
                                    referenced = tw
                                    break
                            if referenced:
                                for u in response.includes['users']:
                                    if u.id == referenced.author_id:
                                        referenced_author = u
                                        break

                                emb.description = referenced.text
                            else:
                                emb.description = tweet.text

                            if referenced_author:
                                emb.title = f"{referenced_author.name} (@{referenced_author.username})"
                                emb.set_author(
                                    name=f"{user.name} (@{user.username}) Retweeted",
                                    icon_url=user.profile_image_url,
                                    url=f"https://twitter.com/{user.username}/status/{tweet.id}"
                                )
                                if referenced:
                                    emb.url = f"https://twitter.com/{referenced_author.username}/status/{referenced.id}"
                            else:
                                emb.title = f"{user.name} (@{user.username}) Retweeted"

                        elif tweet.referenced_tweets[0].type == 'replied_to':
                            referenced: Optional[tweepy.Tweet] = None
                            referenced_author: Optional[tweepy.User] = None
                            for tw in response.includes['tweets']:
                                if tw.id == tweet.referenced_tweets[0].id:
                                    referenced = tw
                                    break
                            if referenced:
                                for u in response.includes['users']:
                                    if u.id == referenced.author_id:
                                        referenced_author = u
                                        break

                            if referenced and referenced_author:
                                emb.set_author(
                                    name=f"Replying to {referenced_author.name} (@{referenced_author.username})",
                                    icon_url=referenced_author.profile_image_url,
                                    url=f"https://twitter.com/{referenced_author.username}/status/{referenced.id}"
                                )

                            emb.title = f"{user.name} (@{user.username})"
                            emb.description = tweet.text
                        elif tweet.referenced_tweets[0].type == 'quoted':
                            referenced: Optional[tweepy.Tweet] = None
                            referenced_author: Optional[tweepy.User] = None
                            for tw in response.includes['tweets']:
                                if tw.id == tweet.referenced_tweets[0].id:
                                    referenced = tw
                                    break
                            if referenced:
                                for u in response.includes['users']:
                                    if u.id == referenced.author_id:
                                        referenced_author = u
                                        break

                            if referenced and referenced_author:
                                emb.set_author(
                                    name=f"Quoting {referenced_author.name} (@{referenced_author.username})",
                                    icon_url=referenced_author.profile_image_url,
                                    url=f"https://twitter.com/{referenced_author.username}/status/{referenced.id}"
                                )

                            emb.title = f"{user.name} (@{user.username})"
                            to_remove = tweet.entities['urls'][-1]['url']
                            emb.description = tweet.text.replace(to_remove, '')
                    else:
                        emb.title = f"{user.name} (@{user.username})"
                        emb.description = tweet.text

                    for m in monitors:
                        channel = self.resolve_channel(m)
                        await channel.send(embed=emb)

    async def on_errors(self, errors: dict) -> None:
        self.bot.log("TWITTER ERRORS:", errors, log_type=LogType.twitter, urgent=True)

    async def on_closed(self, resp: 'aiohttpResponse') -> None:
        self.bot.log("TWITTER CLOSED:", resp, log_type=LogType.twitter, urgent=True)

    async def on_connection_error(self) -> None:
        self.bot.log("TWITTER CONNECTION ERROR", log_type=LogType.twitter, urgent=True)

    async def on_connect(self) -> None:
        self.bot.log("TWITTER CONNECTED", log_type=LogType.twitter, divider=True)

    async def on_disconnect(self) -> None:
        self.bot.log("TWITTER DISCONNECTED", log_type=LogType.twitter, divider=True)

    async def on_exception(self, exception: Exception) -> None:
        self.bot.log("TWITTER EXCEPTION:", error=exception, log_type=LogType.twitter, urgent=True)

    async def on_request_error(self, status_code: int) -> None:
        error = TwitterError(status_code)
        self.bot.log("TWITTER REQUEST ERROR:", error=error, log_type=LogType.twitter)

    def resolve_channel(self, monitor: TwitterMonitor) -> Optional[discord.TextChannel]:
        guild = self.bot.get_guild(monitor.guild_id)

        if guild:
            channel = guild.get_channel(monitor.channel_id)
            return channel

    async def resolve_user(self, id: int) -> Optional[tweepy.User]:
        user = await self.bot.twitter.get_user(id=id, user_fields=user_fields.query)
        return user.data



@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_webhooks=True)
@app_commands.checks.bot_has_permissions(manage_webhooks=True)
class TwitterCog(GroupCog, group_name='twitter', name="twitter"):
    name = "Twitter"
    description = "Commands for handling twitter posts/users."
    help = (
        'Requires `manage_webhooks` permissions. Please note that due to [Twitter API restrictions]'
        '(https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api#v2-access-level), '
        'only a few Twitter accounts can be monitored for new tweets at a time.'
    )
    icon = "\N{HATCHING CHICK}"
    slash_commands = ['monitor', 'monitorlist', 'updatemonitor', 'deletemonitor', 'rulelist']

    monitors: list[TwitterMonitor]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        twitter_bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        self.stream = AsyncStreamingClient(twitter_bearer_token, self.bot, wait_on_rate_limit=True)
        self.bot.twitter = tweepy.asynchronous.AsyncClient(
            bearer_token=twitter_bearer_token,
            wait_on_rate_limit=True
        )

        self.initialize_stream_client.start()

    def cog_unload(self) -> None:
        super().cog_unload()

        self.stream.disconnect()
        self.initialize_stream_client.stop()

    async def update_monitors(self) -> None:
        self.bot.twitter_monitors = await self.bot.db.twitter_monitors.get_all()

    async def update_rules(self) -> None:
        # Handle ensuring the rules are up to date with the twitter stream.
        active_rules = await self.get_rules(self.bot.twitter_monitors)

        # Get current rules
        rules: tweepy.Response = await self.stream.get_rules()
        rules: list[tweepy.StreamRule] = rules.data

        # Compare the active rules to the twitter rules.
        to_delete = set()
        found = set()
        if rules:
            for rule in rules:
                if rule.value not in active_rules:
                    to_delete.add(rule.id)
                else:
                    found.add(rule.value)
        to_add = found.symmetric_difference(active_rules)
        rules_to_add = [tweepy.StreamRule(value=r) for r in to_add] if to_add else []

        # Actually update the twitter rules.
        if to_delete:
            await self.stream.delete_rules(list(to_delete))
        if rules_to_add:
            await self.stream.add_rules(rules_to_add)

    @staticmethod
    async def get_rules(monitors: list[TwitterMonitor]) -> list[str]:
        tmp = {}

        for m in monitors:
            if m.id not in tmp:
                tmp[m.id] = m
            else:
                tmp[m.id].merge_rule(m)

        return [m.rule for m in tmp.values()]

    # ---------- Commands ----------
    @decorators.command(
        name="monitor",
        description="Adds a twitter account to the list of accounts that tweets are posted for.",
        help="Requires `manage_webhooks` permissions to use.",
        icon="\N{LARGE GREEN CIRCLE}"
    )
    @app_commands.describe(
        user="The user to monitor tweets from. This must be the `@username` tag of a twitter user.",
        channel="The channel to post the tweets to. Defaults to the channel the command is used in.",
        retweets="Whether or not to post this user's retweets. Does not include quote retweets. Defaults to False.",
        replies="Whether or not to post this user's replies to other tweets. Defaults to False.",
        quotes="Whether or not to post this user's quote retweets. Defaults to True.",
        retweets_of="Whether or not to include other users' retweets of this user. Defaults to False.",
        replies_of="Whether or not to include other users' replies to this user. Defaults to False.",
    )
    async def twitter_monitor_command(
            self,
            interaction: Interaction,
            user: app_commands.Transform[tweepy.User, transformers.TwitterUserTransformer],
            channel: discord.TextChannel = None,
            retweets: bool = False,
            replies: bool = False,
            quotes: bool = True,
            retweets_of: bool = False,
            replies_of: bool = False,
    ) -> None:
        user: tweepy.User = cast(tweepy.User, user)
        if not channel:
            channel = interaction.channel

        if not await self.bot.db.twitter_monitors.check_exists(user.id, channel):
            rule = TwitterMonitor(
                0, user.id, 0, 0, retweets, replies, quotes, retweets_of, replies_of
            ).rule

            try:
                await self.stream.add_rules(tweepy.StreamRule(rule))
            except Exception:
                emb = self.bot.embeds.get(
                    description=f'Failed to add monitor, Twitter failed to accept it.\n\n{rule}',
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

            await self.bot.db.twitter_monitors.insert(
                user.id, interaction.channel, retweets, replies, quotes, retweets_of, replies_of
            )
            await self.update_monitors()
            await interaction.response.send_message(f"Rule Added: `{rule}`", ephemeral=True)

        else:
            emb = self.bot.embeds.get(
                title=f'{user.name} already monitored in {channel.name}',
                description='Try `/twitter updatemonitor` or `/twitter deletemonitor` first.',
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='updatemonitor',
        description='This command updates an existing twitter monitor.',
        icon='\N{LARGE ORANGE CIRCLE}'
    )
    @app_commands.describe(
        monitor="The monitor to update. If you do not know the ID of you monitor, use `/twitter monitorlist` first.",
        channel="The new channel to move the monitor posts into. Defaults to the previous channel.",
        retweets="Whether or not to post this user's retweets. Does not include quote retweets. Defaults to the previous value.",
        replies="Whether or not to post this user's replies to other tweets. Defaults to the previous value.",
        quotes="Whether or not to post this user's quote retweets. Defaults to the previous value.",
        retweets_of="Whether or not to include other users' retweets of this user. Defaults to the previous value.",
        replies_of="Whether or not to include other users' replies to this user. Defaults to the previous value.",
    )
    async def twitter_monitor_update_command(
            self,
            interaction: Interaction,
            monitor: app_commands.Transform[TwitterMonitor, transformers.TwitterMonitorTransformer],
            channel: discord.TextChannel = None,
            retweets: bool = None,
            replies: bool = None,
            quotes: bool = None,
            retweets_of: bool = None,
            replies_of: bool = None,
    ) -> None:
        monitor: TwitterMonitor = cast(TwitterMonitor, monitor)

        if not await self.bot.db.twitter_monitors.update(
                monitor, channel, retweets, replies, quotes, retweets_of, replies_of
        ):
            emb = self.bot.embeds.get(
                description="At least one changed value must be included in the update request.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        await self.update_monitors()
        await self.update_rules()
        emb = self.bot.embeds.get(description="Updated twitter monitor \N{THUMBS UP SIGN}")
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='monitorlist',
        description="Gets a list of active twitter monitors.",
        help='Requires `manage_webhooks` permissions.',
        icon='\N{LARGE BLUE CIRCLE}'
    )
    async def twitter_monitor_list_command(self, interaction: Interaction) -> None:
        monitors = await self.bot.db.twitter_monitors.get_by_guild(interaction.guild)
        user_ids = [m.twitter_user_id for m in monitors]
        users = await self.bot.twitter.get_users(ids=user_ids)
        tmp = {}
        if users.data:
            for user in users.data:
                tmp[user.id] = f'{user.name} (`@{user.username}`)'
        mapping = {}
        for m in monitors:
            mapping[m.id] = tmp.get(m.twitter_user_id, '')

        emb = self.bot.embeds.get(
            title=f'{interaction.guild} Twitter Monitors',
            description='\n'.join(f'`{k}` {v}' for k, v in mapping.items())
        )
        await interaction.response.send_message(embed=emb)

    @decorators.command(
        name='rulelist',
        description='Gets a list of the actual rules that the Twitter API uses for capturing tweets.',
        icon='\N{LARGE BLUE CIRCLE}'
    )
    async def twitter_rule_list_command(self, interaction: Interaction) -> None:
        monitors = await self.bot.db.twitter_monitors.get_by_guild(interaction.guild)
        rules = await self.get_rules(monitors)
        emb = self.bot.embeds.get(
            title=f"{interaction.guild} Twitter Rules",
            description='\n'.join(f'`{r}`' for r in rules)
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='deletemonitor',
        description='Deletes an active twitter monitor.',
        help='Requires `manage_webhooks` permissions.',
        icon='\N{LARGE RED CIRCLE}'
    )
    @app_commands.describe(
        monitor="The monitor to be deleted."
    )
    async def twitter_monitor_delete_command(
            self,
            interaction: Interaction,
            monitor: app_commands.Transform[TwitterMonitor, transformers.TwitterMonitorTransformer]
    ) -> None:
        monitor: TwitterMonitor = cast(TwitterMonitor, monitor)

        if not await self.bot.db.twitter_monitors.delete_by_id(monitor.id):
            emb = self.bot.embeds.get(
                description="Monitor could not be deleted.",
                color=discord.Color.brand_red()
            )
        else:
            emb = self.bot.embeds.get(
                description="Monitor deleted successfully."
            )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    # ---------- Tasks ----------
    @tasks.loop(seconds=1, count=1)
    async def initialize_stream_client(self) -> None:
        # Start the stream listener.
        self.stream.filter(
            tweet_fields=tweet_fields.query,
            user_fields=user_fields.query,
            media_fields=media_fields.query,
            expansions='referenced_tweets.id.author_id,attachments.media_keys'
        )

    @initialize_stream_client.before_loop
    async def before_loop(self) -> None:
        await self.update_monitors()
        await self.update_rules()
        await self.bot.wait_until_ready()


async def setup(bot: Bot) -> None:
    await bot.add_cog(TwitterCog(bot), guilds=[bot.GUILD])
