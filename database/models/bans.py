import datetime
from dataclasses import dataclass
from typing import Optional, List

import asyncpg
from discord import Guild, User
from discord.utils import utcnow


@dataclass
class Ban:
    ban_id: int
    user_id: int
    user_name: str
    user_avatar: str
    guild_id: int
    banner_id: int
    ban_ts: datetime.datetime
    active: bool
    duration: Optional[datetime.timedelta] = None
    reason: Optional[str] = None

    @staticmethod
    def schema():
        return '''CREATE TABLE IF NOT EXISTS bans (
            ban_id serial PRIMARY KEY,
            user_id bigint NOT NULL,
            user_name text NOT NULL,
            user_avatar text NOT NULL,
            guild_id bigint NOT NULL,
            banner_id bigint,
            ban_ts timestamp with time zone NOT NULL,
            duration interval,
            reason text,
            active bool DEFAULT false NOT NULL
        );
        '''

    @property
    def actionable(self):
        if self.duration:
            if utcnow() > self.ban_ts + self.duration:
                return True
        return False

    @property
    def unban_date(self) -> Optional[datetime.datetime]:
        return self.ban_ts + self.duration if self.duration else None


class Bans:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create(self) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(Ban.schema())

    async def deactivate_by_id(self, id: int) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.fetch('''UPDATE bans SET active=$1 WHERE ban_id=$2;''', False, id)

    async def deactivate_all_for_user_in_guild(self, user: User, guild: Guild) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    '''UPDATE bans SET active=$1 WHERE user_id=$2 AND guild_id=$3;''',
                    False, user.id, guild.id
                )

    async def insert(self, user: User, guild: Guild, banner: User = None, duration: Optional[datetime.timedelta] = None,
                     reason: Optional[str] = None) -> None:
        await self.deactivate_all_for_user_in_guild(user=user, guild=guild)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    '''INSERT INTO bans (user_id, user_name, user_avatar, guild_id, banner_id, ban_ts, duration, reason, active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);''',
                    user.id, str(user), user.display_avatar.url, guild.id,
                    banner.id if banner is not None else banner, utcnow(), duration, reason, True
                )

    async def get_all_active(self) -> List[Ban]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE active=$1;''', True)
                return [Ban(**b) for b in res]

    async def get_all_active_for_guild(self, guild: Guild) -> List[Ban]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE guild_id=$1 AND active=$2;''', guild.id, True)
                return [Ban(**b) for b in res]

    async def get_all_active_ban_users_for_guild(self, guild: Guild, query: str) -> List[Ban]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch(
                    '''SELECT * FROM bans WHERE guild_id=$1 AND active=$2 AND LOWER(user_name) LIKE LOWER($3) LIMIT $4;''',
                    guild.id, True, f'%{query}%', 25
                )
                return [Ban(**b) for b in res]

    async def get_active_for_user_in_guild(self, user: User, guild: Guild) -> Ban:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchrow(
                    '''SELECT * FROM bans WHERE user_id=$1 AND guild_id=$2 AND active=$3;''',
                    user.id, guild.id, True
                )
                return Ban(**res) if res else res

    async def get_active_for_username_in_guild(self, user: str, guild: Guild) -> Ban:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchrow(
                    '''SELECT * FROM bans WHERE user_name=$1 AND guild_id=$2 AND active=$3;''',
                    user, guild.id, True
                )
                return Ban(**res) if res else res

    async def get_all_for_user_in_guild(self, user: User, guild: Guild) -> List[Ban]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE user_id=$1 AND guild_id=$2;''', user.id, guild.id)
                return [Ban(**b) for b in res]

    async def get_all_for_user(self, user: User) -> List[Ban]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE user_id=$1;''', user.id)
                return [Ban(**b) for b in res]

    async def get_most_recent_for_user(self, user: User) -> Optional[Ban]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(
                    '''SELECT ban_ts FROM bans WHERE user_id=$1 ORDER BY ban_ts DESC LIMIT 1;''',
                    user.id
                )
