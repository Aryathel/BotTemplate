from functools import wraps
from secrets import SystemRandom

import asyncpg

_id_gen = SystemRandom()


def pooled_query(method):
    @wraps(method)
    async def decorator(self, *args, **kwargs):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await method(self, conn, *args, **kwargs)

    return decorator


def pooled_with_new_id_safe(table: str):
    def inner(func):
        @wraps(func)
        @pooled_query
        async def decorator(wrapped_self, conn: asyncpg.Connection, *args, **kwargs):
            id = get_random_bigint()
            while await id_is_taken(conn, id, table):
                id = get_random_bigint()

            return await func(wrapped_self, conn, id, *args, **kwargs)

        return decorator

    return inner


async def id_is_taken(conn: asyncpg.Connection, id: int, table: str) -> bool:
    return await conn.fetchval(f'''SELECT EXISTS(SELECT 1 FROM {table} WHERE id=$1);''', id)


def get_random_bigint() -> int:
    return _id_gen.randint(0, 9223372036854775807)