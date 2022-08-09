import re
from dataclasses import dataclass
from typing import Optional

import asyncpg
import discord

from ..utils import pooled_query, pooled_with_new_id_safe

p = re.compile(r"^from:(?P<user_id>\d+)\s*?(?P<noretweets>-is:retweet)?\s*?(?P<noreplies>-is:reply)?\s*?(?P<noquotes>-is:quote)?\s*?(OR\s*?retweets_of:(?P<retweetsof>\d+))?\s*?(OR\s*?to:(?P<repliesof>\d+))?$")


@dataclass
class TwitterMonitor:
    id: int
    twitter_user_id: int
    guild_id: int
    channel_id: int
    retweets: bool
    replies: bool
    quotes: bool
    retweets_of: bool
    replies_of: bool

    @staticmethod
    def schema() -> str:
        return '''CREATE TABLE IF NOT EXISTS twitter_monitors (
            id bigint PRIMARY KEY,
            twitter_user_id bigint NOT NULL,
            guild_id bigint NOT NULL,
            channel_id bigint NOT NULL,
            retweets boolean NOT NULL,
            replies boolean NOT NULL,
            quotes boolean NOT NULL,
            retweets_of boolean NOT NULL,
            replies_of boolean NOT NULL
        );'''

    @property
    def rule(self) -> str:
        rule = f"from:{self.twitter_user_id}"
        if not self.retweets:
            rule += ' -is:retweet'
        if not self.replies:
            rule += ' -is:reply'
        if not self.quotes:
            rule += ' -is:quote'
        if self.retweets_of:
            rule += f' OR retweets_of:{self.twitter_user_id}'
        if self.replies_of:
            rule += f' OR to:{self.twitter_user_id}'

        return rule

    @classmethod
    def from_rule(cls, rule: str) -> 'TwitterMonitor':
        matches = p.search(rule)
        try:
            return cls(
                id=-1,
                guild_id=-1,
                channel_id=-1,
                twitter_user_id=int(matches.group('user_id')),
                retweets=not bool(matches.group('noretweets')),
                replies=not bool(matches.group('noreplies')),
                quotes=not bool(matches.group('noquotes')),
                retweets_of=bool(matches.group('retweetsof')),
                replies_of=bool(matches.group('repliesof')),
            )
        except Exception:
            raise ValueError(f"Invalid rule received: {rule}")

    def merge_rule(self, monitor: 'TwitterMonitor') -> None:
        if monitor.retweets and not self.retweets:
            self.retweets = True
        if monitor.replies and not self.replies:
            self.replies = True
        if monitor.quotes and not self.quotes:
            self.quotes = True
        if monitor.retweets_of and not self.retweets_of:
            self.retweets_of = True
        if monitor.replies_of and not self.replies_of:
            self.replies_of = True

    def __str__(self) -> str:
        return f"\"{self.rule}\""

    def __repr__(self) -> str:
        return self.__str__()


class TwitterMonitors:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @pooled_query
    async def create(self, conn: asyncpg.Connection) -> None:
        await conn.execute(TwitterMonitor.schema())

    @pooled_with_new_id_safe(table='twitter_monitors')
    async def insert(
            self,
            conn: asyncpg.Connection,
            id: int,
            user_id: int,
            channel: discord.TextChannel,
            retweets: bool,
            replies: bool,
            quotes: bool,
            retweets_of: bool,
            replies_of: bool
    ) -> int:
        await conn.execute(
            '''INSERT INTO twitter_monitors
            (id, twitter_user_id, guild_id, channel_id, retweets, replies, quotes, retweets_of, replies_of)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
            ''',
            id, user_id, channel.guild.id, channel.id, retweets, replies, quotes, retweets_of, replies_of
        )

        return id

    @pooled_query
    async def get_all(self, conn: asyncpg.Connection) -> list[TwitterMonitor]:
        rows = await conn.fetch('''SELECT * FROM twitter_monitors;''')
        return [TwitterMonitor(**r) for r in rows]

    @pooled_query
    async def get_by_id(self, conn: asyncpg.Connection, id: int) -> Optional[TwitterMonitor]:
        row = await conn.fetchrow('''SELECT * FROM twitter_monitors WHERE id=$1;''', id)
        if row:
            return TwitterMonitor(**row)

    @pooled_query
    async def get_by_guild(self, conn: asyncpg.Connection, guild: discord.Guild) -> list[TwitterMonitor]:
        rows = await conn.fetch('''SELECT * FROM twitter_monitors WHERE guild_id=$1;''', guild.id)
        return [TwitterMonitor(**r) for r in rows]

    @pooled_query
    async def update(
            self,
            conn: asyncpg.Connection,
            monitor: TwitterMonitor,
            channel: discord.TextChannel,
            retweets: bool,
            replies: bool,
            quotes: bool,
            retweets_of: bool,
            replies_of: bool
    ) -> bool:
        i = 1
        updates = []
        values = []

        if channel:
            if not monitor.guild_id == channel.guild.id:
                updates.append(f"guild_id=${i}")
                values.append(channel.guild.id)
                i += 1
            if not monitor.channel_id == channel.id:
                updates.append(f"channel_id=${i}")
                values.append(channel.id)
                i += 1
        if retweets is not None and not monitor.retweets == retweets:
            updates.append(f"retweets=${i}")
            values.append(retweets)
            i += 1
        if replies is not None and not monitor.replies == replies:
            updates.append(f"replies=${i}")
            values.append(replies)
            i += 1
        if quotes is not None and not monitor.quotes == quotes:
            updates.append(f"quotes=${i}")
            values.append(quotes)
            i += 1
        if retweets_of is not None and not monitor.retweets_of == retweets_of:
            updates.append(f"retweets_of=${i}")
            values.append(retweets_of)
            i += 1
        if replies_of is not None and not monitor.replies_of == replies_of:
            updates.append(f"replies_of=${i}")
            values.append(replies_of)
            i += 1

        if not updates:
            return False

        await conn.execute(f'''UPDATE twitter_monitors SET {", ".join(updates)} WHERE id=${i};''', *values, monitor.id)
        return True

    @pooled_query
    async def check_exists(self, conn: asyncpg.Connection, user_id: int, channel: discord.TextChannel) -> bool:
        return await conn.fetchval(
            '''SELECT EXISTS(SELECT 1 FROM twitter_monitors WHERE twitter_user_id=$1 AND guild_id=$2 AND channel_id=$3);''',
            user_id, channel.guild.id, channel.id
        )

    @pooled_query
    async def delete_by_id(self, conn: asyncpg.Connection, id: int) -> bool:
        if not await conn.fetchval('''SELECT EXISTS(SELECT 1 FROM twitter_monitors WHERE id=$1);''', id):
            return False

        await conn.execute('''DELETE FROM twitter_monitors WHERE id=$1;''', id)
        return True
