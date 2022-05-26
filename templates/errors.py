from typing import Any, Type

import discord
from discord import app_commands
from .types import AppCommandOptionType


# ---------- Transformer Error ----------
class TransformerError(app_commands.AppCommandError):
    def __init__(self, value: Any, opt_type: AppCommandOptionType, transformer: Type[app_commands.Transformer]):
        self.value: Any = value
        self.type: AppCommandOptionType = opt_type
        self.transformer: Type[app_commands.Transformer] = transformer

        try:
            result_type = transformer.transform.__annotations__['return']
        except KeyError:
            name = transformer.__name__
            if name.endswith('Transformer'):
                result_type = name[:-11]
            else:
                result_type = name
        else:
            if isinstance(result_type, type):
                result_type = result_type.__name__

        super().__init__(f'Failed to convert {value} to {result_type!s}')