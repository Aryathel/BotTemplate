import asyncpg

from .models.bans import Bans
from .models.warns import Warns
from .models.role_reaction_messages import RoleReactionMessages
from .models.role_reaction import RoleReactions
from .models.twitter_monitors import TwitterMonitors


class Client:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

        # Get models.
        self.bans = Bans(self.pool)
        self.warns = Warns(self.pool)
        self.role_reaction_messages = RoleReactionMessages(self.pool)
        self.role_reactions = RoleReactions(self.pool)
        self.twitter_monitors = TwitterMonitors(self.pool)

    async def initialize(self):
        # Create model tables if nonexistent.
        await self.bans.create()
        await self.warns.create()
        await self.role_reaction_messages.create()
        await self.role_reactions.create()
        await self.twitter_monitors.create()
