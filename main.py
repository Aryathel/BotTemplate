import os
import discord

from templates import Bot
from utils import EmbedFactory

if __name__ == "__main__":
    emb_fac = EmbedFactory(
        color=discord.Colour.from_str(os.getenv('BOT_COLOR'))
    )

    bot = Bot(
        command_prefix='!',
        description="This is Arya's template Discord.py v2.0 bot!",
        token=os.getenv('BOT_TOKEN'),
        guild=discord.Object(id=int(os.getenv('BOT_GUILD'))),
        owner_id=int(os.getenv('BOT_OWNER')),
        db_host=os.getenv('POSTGRES_DB_HOST'),
        db_port=os.getenv('POSTGRES_DB_PORT'),
        db_name=os.getenv('POSTGRES_DB_NAME'),
        db_user=os.getenv('POSTGRES_DB_USER'),
        db_pass=os.getenv('POSTGRES_DB_PASS'),
        embed_factory=emb_fac
    )
    bot.run()
