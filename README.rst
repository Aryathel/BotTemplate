Discord.py v2.0 Template
========================

This is a template that I intend to use as the core for other bot projects,
or for generally messing around with making Discord bots. This project was
inspired by the development efforts of the `Discord.py <https://github.com/Rapptz/discord.py>`_
team in developing the `v2.0` release for the newest Discord API version.

Disclaimer
==========

This is all very much a work in progress.

Environment Settings
====================

The project is currently configured to use a ``.env`` file for configuring the environment.
By creating the ``.env`` file in the root of the project, you can
use the following format to configure the program::

    # Discord Bot Settings
    BOT_TOKEN=your_bot_token
    BOT_DESCRIPTION="A simple description."
    BOT_GUILD=0000000
    BOT_OWNER=0000000
    BOT_COLOR=#000000

    # Cogs To Load
    COGS_DND=True
    COGS_MISC=True
    COGS_MODERATION=True
    COGS_TWITTER=False

    # Database Connection Info
    POSTGRES_DB_HOST=localhost
    POSTGRES_DB_PORT=5432
    POSTGRES_DB_NAME=bot_testing
    POSTGRES_DB_USER=username
    POSTGRES_DB_PASS=password

    # Twitter Specific Config
    TWITTER_BEARER_TOKEN=bearer_token

Settings Info
-------------
Individual settings information.

Discord Bot Settings
~~~~~~~~~~~~~~~~~~~~
    * ``BOT_TOKEN``: The Discord-provided token the bot uses to authenticate with the discord servers.
    * ``BOT_DESCRIPTION``: A short description of the bot.
    * ``BOT_GUILD``: The ID of the primary guild the bot belongs to.
    * ``BOT_OWNER``: The ID of the owner of the bot (used to limit certain developer commands).
    * ``BOT_COLOR``: The default color for the bot, as a hex string (used for coloring embed messages).

Cogs To Load
~~~~~~~~~~~~
    A collection of what cogs to load/not load. By default, this includes
    ``COGS_DND``, ``COGS_MISC``, ``COGS_MODERATION``, and ``COGS_TWITTER``.
    However, custom cogs can be added by adding a cog to the `cogs` folder,
    then adding a new environment variable to this collection called
    ``COGS_FILENAME``, where ``FILENAME`` is the name of your cog file in
    all caps. Note that your cogs should have all lowercase file names.

Database Connection Info
~~~~~~~~~~~~~~~~~~~~~~~~
    This project uses a PostgreSQL database to persist data. These options
    are pretty self explanatory, and give the bot the information it needs to
    connect to the database.

Twitter Specific Config
~~~~~~~~~~~~~~~~~~~~~~~
    Config options specific to the ``twitter`` cog.

    * ``TWITTER_BEARER_TOKEN``: The bearer token that the Twitter API provides for their API v2 endpoints.