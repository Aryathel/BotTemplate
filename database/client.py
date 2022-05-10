import asyncpg

from .models.bans import Bans


class Client:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

        # Get models.
        self.bans = Bans(self.pool)

    async def initialize(self):
        await self.bans.create()
