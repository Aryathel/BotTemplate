from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from asyncpg import Connection, Pool
import discord

from ..utils import pooled_query, pooled_with_new_id_safe


@dataclass
class RoleReactionMessage:
    id: int
    message_id: int
    channel_id: int
    guild_id: int
    active: bool

    @staticmethod
    def schema() -> str:
        return f'''CREATE TABLE IF NOT EXISTS role_reaction_messages (
            id bigint PRIMARY KEY,
            message_id bigint NOT NULL,
            channel_id bigint NOT NULL,
            guild_id bigint NOT NULL,
            active bool DEFAULT true NOT NULL
        );'''


class RoleReactionMessages:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    @pooled_query
    async def create(self, conn: Connection) -> None:
        await conn.execute(RoleReactionMessage.schema())

    @pooled_query
    async def deactivate_by_id(self, conn: Connection, id: int) -> None:
        await conn.execute('''UPDATE role_reaction_messages SET active=$1 WHERE id=$2;''', False, id)

    @pooled_query
    async def activate_by_id(self, conn: Connection, id: int) -> None:
        await conn.execute('''UPDATE role_reaction_messages SET active=$1 WHERE id=$2;''', True, id)

    @pooled_with_new_id_safe(table='role_reaction_messages')
    async def insert(
            self,
            conn: Connection,
            id: int,
            message_id: int,
            channel_id: int,
            guild_id: int,
    ) -> int:
        await conn.execute(
            '''INSERT INTO role_reaction_messages (id, message_id, channel_id, guild_id) 
            VALUES ($1, $2, $3, $4);''',
            id, message_id, channel_id, guild_id
        )
        return id

    @pooled_query
    async def get_by_id(self, conn: Connection, id: int) -> Optional[RoleReactionMessage]:
        row = await conn.fetchrow('''SELECT * FROM role_reaction_messages WHERE id=$1;''', id)
        if row:
            return RoleReactionMessage(**row)

    @pooled_query
    async def get_active_by_guild(self, conn: Connection, guild: discord.Guild) -> list[RoleReactionMessage]:
        rows = await conn.fetch(
            '''SELECT * FROM role_reaction_messages WHERE guild_id=$1 AND active=$2;''',
            guild.id, True
        )
        return [RoleReactionMessage(**r) for r in rows]

    @pooled_query
    async def get_by_message_id(self, conn: Connection, id: int) -> Optional[RoleReactionMessage]:
        row = await conn.fetchrow('''SELECT * FROM role_reaction_messages WHERE message_id=$1;''', id)
        if row:
            return RoleReactionMessage(**row)

    @pooled_query
    async def delete_by_id(self, conn: Connection, id: int) -> None:
        await conn.execute('''DELETE FROM role_reaction_messages WHERE id=$1;''', id)
