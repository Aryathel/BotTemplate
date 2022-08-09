from typing import Optional, TYPE_CHECKING, Union
from dataclasses import dataclass

import asyncpg
import discord

from ..utils import pooled_query, pooled_with_new_id_safe

if TYPE_CHECKING:
    from templates import Emoji, Interaction


@dataclass
class RoleReaction:
    id: int
    role_reaction_message_id: int
    role_id: int
    emoji_name: Optional[str]
    emoji_id: Optional[int]

    role: Optional[discord.Role] = None
    emoji: Optional[Union[str, discord.Emoji]] = None

    @property
    def is_custom(self) -> bool:
        if self.emoji_id:
            return True
        return False

    @staticmethod
    def schema() -> str:
        return '''CREATE TABLE IF NOT EXISTS role_reactions (
            id bigint PRIMARY KEY,
            role_reaction_message_id bigint NOT NULL,
            role_id bigint NOT NULL,
            emoji_name text NOT NULL,
            emoji_id bigint,
            CONSTRAINT fk_rr_msg_id FOREIGN KEY(role_reaction_message_id)
            REFERENCES role_reaction_messages(id)
        );'''

    def populate(self, interaction: 'Interaction') -> None:
        self.role = interaction.guild.get_role(self.role_id)
        if self.is_custom:
            self.emoji = interaction.client.get_emoji(self.emoji_id)
        else:
            self.emoji = self.emoji_name


class RoleReactions:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @pooled_query
    async def create(self, conn: asyncpg.Connection) -> None:
        await conn.execute(RoleReaction.schema())

    @pooled_with_new_id_safe(table='role_reactions')
    async def insert(
            self,
            conn: asyncpg.Connection,
            id: int,
            role_id: int,
            emoji: 'Emoji',
            role_reaction_message_id: int
    ) -> int:
        await conn.execute(
            f'''INSERT INTO role_reactions (
            id, role_reaction_message_id, role_id, emoji_id, emoji_name
            ) VALUES ($1, $2, $3, $4, $5);''',
            id, role_reaction_message_id, role_id, emoji.discord_emoji.id if emoji.is_custom else None, emoji.name
        )
        return id

    @pooled_query
    async def get_by_id(self, conn: asyncpg.Connection, id: int) -> Optional[RoleReaction]:
        row = await conn.fetchrow('''SELECT * FROM role_reactions WHERE id=$1;''', id)
        if row:
            return RoleReaction(**row)

    @pooled_query
    async def get_by_role_reaction_message_id(self, conn: asyncpg.Connection, id: int) -> list[RoleReaction]:
        rows = await conn.fetch('''SELECT * FROM role_reactions WHERE role_reaction_message_id=$1;''', id)
        return [RoleReaction(**r) for r in rows]

    @pooled_query
    async def delete_by_id(self, conn: asyncpg.Connection, id: int) -> None:
        await conn.execute('''DELETE FROM role_reactions WHERE id=$1;''', id)

    @pooled_query
    async def delete_by_role_reaction_message_id(self, conn: asyncpg.Connection, id: int) -> None:
        await conn.execute('''DELETE FROM role_reactions WHERE role_reaction_message_id=$1;''', id)
