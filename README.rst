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
use the following format to configure the program.

..code-block::
    :caption: ``.env`` file format

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

