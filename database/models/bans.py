import datetime
from dataclasses import dataclass
from typing import Optional, List, cast

import asyncpg
from asyncpg import Connection
from discord import Guild, User
from discord.utils import utcnow

from ..utils import pooled_query


@dataclass
class Ban:
    id: int
    user_id: int
    user_name: str
    user_avatar: str
    guild_id: int
    banned_by: int
    ts: datetime.datetime
    active: bool
    duration: Optional[datetime.timedelta] = None
    reason: Optional[str] = None

    @staticmethod
    def schema() -> str:
        return '''CREATE TABLE IF NOT EXISTS bans (
            id serial PRIMARY KEY,
            user_id bigint NOT NULL,
            user_name text NOT NULL,
            user_avatar text NOT NULL,
            guild_id bigint NOT NULL,
            banned_by bigint,
            ts timestamp with time zone NOT NULL,
            duration interval,
            reason text,
            active bool DEFAULT false NOT NULL
        );
        '''

    @property
    def actionable(self):
        if self.duration:
            if utcnow() > self.ts + self.duration:
                return True
        return False

    @property
    def unban_date(self) -> Optional[datetime.datetime]:
        return self.ts + self.duration if self.duration else None


class Bans:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @pooled_query
    async def create(self, conn: Connection) -> None:
        await conn.execute(Ban.schema())

    @pooled_query
    async def deactivate_by_id(self, conn: Connection, id: int) -> None:
        await conn.execute('''UPDATE bans SET active=$1 WHERE ban_id=$2;''', False, id)

    @pooled_query
    async def deactivate_all_for_user_in_guild(self, conn: Connection, user: User, guild: Guild) -> None:
        await conn.execute(
            '''UPDATE bans SET active=$1 WHERE user_id=$2 AND guild_id=$3;''',
            False, user.id, guild.id
        )

    @pooled_query
    async def deactivate_all_for_users_in_guild(self, conn: Connection, users: List[User], guild: Guild) -> None:
        conn = cast(asyncpg.Connection, conn)
        await conn.executemany(
            '''UPDATE bans SET active=$1 WHERE user_id=$2 AND guild_id=$3;''',
            [(False, user.id, guild.id) for user in users]
        )

    @pooled_query
    async def insert(self, conn: Connection, user: User, guild: Guild, banner: User = None, duration: Optional[datetime.timedelta] = None,
                     reason: Optional[str] = None, active: bool = True) -> None:
        await self.deactivate_all_for_user_in_guild(user=user, guild=guild)

        await conn.execute(
            '''INSERT INTO bans (user_id, user_name, user_avatar, guild_id, banned_by, ts, duration, reason, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);''',
            user.id, str(user), user.display_avatar.url, guild.id,
            banner.id if banner is not None else banner, utcnow(), duration, reason, active
        )

    @pooled_query
    async def insert_multi(self, conn: Connection, users: List[User], guild: Guild, banner: User = None, duration: Optional[datetime.timedelta] = None,
                     reason: Optional[str] = None, active: bool = True) -> None:
        await self.deactivate_all_for_users_in_guild(users=users, guild=guild)

        banner_id = banner.id if banner is not None else banner
        dt = utcnow()

        await conn.executemany(
            '''INSERT INTO bans (user_id, user_name, user_avatar, guild_id, banned_by, ts, duration, reason, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);''',
            [(user.id, str(user), user.display_avatar.url, guild.id,
            banner_id, dt, duration, reason, active) for user in users]
        )

    @pooled_query
    async def get_all_active(self, conn: Connection) -> List[Ban]:
        res = await conn.fetch('''SELECT * FROM bans WHERE active=$1;''', True)
        return [Ban(**b) for b in res]

    @pooled_query
    async def get_all_active_for_guild(self, conn: Connection, guild: Guild) -> List[Ban]:
        res = await conn.fetch('''SELECT * FROM bans WHERE guild_id=$1 AND active=$2;''', guild.id, True)
        return [Ban(**b) for b in res]

    @pooled_query
    async def get_all_active_ban_users_for_guild(self, conn: Connection, guild: Guild, query: str) -> List[Ban]:
        res = await conn.fetch(
            '''SELECT * FROM bans WHERE guild_id=$1 AND active=$2 AND LOWER(user_name) LIKE LOWER($3) LIMIT $4;''',
            guild.id, True, f'%{query}%', 25
        )
        return [Ban(**b) for b in res]

    @pooled_query
    async def get_active_for_user_in_guild(self, conn: Connection, user: User, guild: Guild) -> Ban:
        res = await conn.fetchrow(
            '''SELECT * FROM bans WHERE user_id=$1 AND guild_id=$2 AND active=$3;''',
            user.id, guild.id, True
        )
        return Ban(**res) if res else res

    @pooled_query
    async def get_active_for_username_in_guild(self, conn: Connection, user: str, guild: Guild) -> Ban:
        res = await conn.fetchrow(
            '''SELECT * FROM bans WHERE user_name=$1 AND guild_id=$2 AND active=$3;''',
            user, guild.id, True
        )
        return Ban(**res) if res else res

    @pooled_query
    async def get_all_for_user_in_guild(self, conn: Connection, user: User, guild: Guild) -> List[Ban]:
        res = await conn.fetch('''SELECT * FROM bans WHERE user_id=$1 AND guild_id=$2;''', user.id, guild.id)
        return [Ban(**b) for b in res]

    @pooled_query
    async def get_all_for_user(self, conn: Connection, user: User) -> List[Ban]:
        res = await conn.fetch('''SELECT * FROM bans WHERE user_id=$1;''', user.id)
        return [Ban(**b) for b in res]

    @pooled_query
    async def get_most_recent_for_user(self, conn: Connection, user: User) -> Optional[Ban]:
        return await conn.fetchval(
            '''SELECT ban_ts FROM bans WHERE user_id=$1 ORDER BY ts DESC LIMIT 1;''',
            user.id
        )
