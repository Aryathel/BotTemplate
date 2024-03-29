from typing import Any, Type

from discord import app_commands

from .types import AppCommandOptionType, TWITTER_HTTP_ERRORS


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


# ---------- Twitter Error ----------
class TwitterError(Exception):
    def __init__(self, status_code: int) -> None:
        name, message = TWITTER_HTTP_ERRORS.get(status_code, ("Unknown Error", "An unknown Twitter error occurred."))
        msg = f"{status_code} {name.upper()}: {message}"

        super().__init__(msg)


# ---------- DnD Errors ----------
class SchemaError(Exception):
    def __init__(self, *, endpoint: str = None, index: str = None) -> None:
        if endpoint:
            if index:
                super().__init__(f'No schema for `{index}` response at endpoint `{endpoint}`')
            else:
                super().__init__(f"No response schema found for endpoint `{endpoint}`")
        elif index:
            super().__init__(f"No schema found for index `{index}`")
