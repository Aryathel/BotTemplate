import os
import logging

import discord

from templates import Bot
from utils import EmbedFactory


logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    cogs = ['cogs.admin']
    for k, v in os.environ.items():
        if k.startswith('COGS_') and not v == 'False':
            cogs.append(k.lower().replace('_', '.'))

    bot = Bot(
        command_prefix='!',
        description=os.getenv('BOT_DESCRIPTION'),

        token=os.getenv('BOT_TOKEN'),
        guild=discord.Object(id=int(os.getenv('BOT_GUILD'))),
        owner_id=int(os.getenv('BOT_OWNER')),

        db_host=os.getenv('POSTGRES_DB_HOST'),
        db_port=os.getenv('POSTGRES_DB_PORT'),
        db_name=os.getenv('POSTGRES_DB_NAME'),
        db_user=os.getenv('POSTGRES_DB_USER'),
        db_pass=os.getenv('POSTGRES_DB_PASS'),

        embed_factory=EmbedFactory(
            color=discord.Colour.from_str(os.getenv('BOT_COLOR'))
        ),

        cogs=cogs,
        cog_params={
            "Twitter": {
                "bearer_token": os.environ.get('TWITTER_BEARER_TOKEN')
            }
        }
    )
    bot.run()
