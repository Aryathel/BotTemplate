from dataclasses import dataclass
import datetime
from typing import Optional

from discord import Member, Guild
from discord.utils import utcnow


@dataclass
class Ban:
    ban_id: int
    user_id: int
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
            user_id bigint,
            guild_id bigint NOT NULL,
            banner_id bigint,
            ban_ts timestamp with time zone NOT NULL,
            duration interval,
            reason text,
            active bool DEFAULT false NOT NULL
        );
        '''


class Bans:
    def __init__(self, pool):
        self.pool = pool

    async def create(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(Ban.schema())

    async def deactivate_all_for_user(self, user: Member, guild: Guild):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    '''UPDATE bans SET active=$1 WHERE user_id=$2 AND guild_id=$3;''',
                    False, user.id, guild.id
                )

    async def insert(self, user: Member, guild: Guild, banner: Member = None, duration: Optional[datetime.timedelta] = None,
                     reason: Optional[str] = None):
        await self.deactivate_all_for_user(user=user, guild=guild)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    '''INSERT INTO bans (user_id, guild_id, banner_id, ban_ts, duration, reason, active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7);''',
                    user.id, guild.id, banner.id if banner is not None else banner, utcnow(), duration, reason, True
                )

    async def get_all_for_guild(self, guild: Guild):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE guild_id=$1 AND active=$2;''', guild.id, True)
                return [Ban(**b) for b in res]

    async def get_all_for_user(self, user: Member, guild: Guild):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE user_id=$1 AND guild_id=$2;''', user.id, guild.id)
                return [Ban(**b) for b in res]

    async def get_all_for_user_global(self, user: Member):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetch('''SELECT * FROM bans WHERE user_id=$1;''', user.id)
                return [Ban(**b) for b in res]
