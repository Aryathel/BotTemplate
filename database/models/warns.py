from dataclasses import dataclass
import datetime
from typing import Optional

import asyncpg
from asyncpg import Connection
from discord import User, Guild
from discord.utils import utcnow

from ..utils import pooled_query


@dataclass
class Warn:
    id: int
    reason: str
    ts: datetime.datetime
    user_id: int
    user_name: str
    user_avatar: str
    warned_by_id: int
    warned_by_name: str
    warned_by_avatar: str
    guild_id: int

    @staticmethod
    def schema() -> str:
        return '''CREATE TABLE IF NOT EXISTS warns (
            id serial PRIMARY KEY,
            user_id bigint NOT NULL,
            user_name text NOT NULL,
            user_avatar text NOT NULL,
            guild_id bigint NOT NULL,
            warned_by_id bigint NOT NULL,
            warned_by_name text NOT NULL,
            warned_by_avatar text NOT NULL,
            ts timestamp with time zone NOT NULL,
            reason text
        );
        '''


class Warns:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @pooled_query
    async def create(self, conn: Connection) -> None:
        await conn.execute(Warn.schema())

    @pooled_query
    async def insert(self, conn: Connection, user: User, guild: Guild, warner: User, reason: str = None) -> int:
        return await conn.fetchval(
            '''INSERT INTO warns (user_id, user_name, user_avatar, guild_id, warned_by_id, warned_by_name, warned_by_avatar, ts, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id;''',
            user.id, str(user), user.display_avatar.url, guild.id, warner.id, str(warner), warner.display_avatar.url, utcnow(), reason
        )

    @pooled_query
    async def get_by_id(self, conn: Connection, id: int) -> Optional[Warn]:
        res = await conn.fetchrow('''SELECT * FROM warns WHERE id=$1;''', id)
        if res:
            return Warn(**res)

    @pooled_query
    async def get_all_for_guild(self, conn: Connection, guild: Guild) -> list[Warn]:
        res = await conn.fetch('''SELECT * FROM warns WHERE guild_id=$1;''', guild.id)
        return [Warn(**w) for w in res]

    @pooled_query
    async def get_all_for_user_in_guild(self, conn: Connection, user: User, guild: Guild) -> list[Warn]:
        res = await conn.fetch('''SELECT * FROM warns WHERE user_id=$1 AND guild_id=$2;''', user.id, guild.id)
        return [Warn(**w) for w in res]

    @pooled_query
    async def delete_by_id(self, conn: Connection, id: int) -> bool:
        if await conn.fetchval('''SELECT EXISTS(SELECT 1 FROM warns WHERE id=$1);''', id):
            await conn.execute('''DELETE FROM warns WHERE id=$1;''', id)
            return True
        return False
