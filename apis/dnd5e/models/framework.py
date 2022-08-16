import abc
from typing import Any, Mapping, Optional

from marshmallow import Schema, fields as fs, ValidationError

from templates import Interaction
from utils import EmbedFactory, Menu


class UnionField(fs.Field):
    def __init__(self, fields: list[fs.Field] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if fields:
            self.fields = fields
        else:
            raise AttributeError('No types provided for UnionField')

    def _deserialize(
        self,
        value: Any,
        attr: Optional[str],
        data: Optional[Mapping[str, Any]],
        **kwargs,
    ):
        errors = []
        for field in self.fields:
            try:
                value = field._deserialize(value, attr, data, **kwargs)
                return value
            except ValidationError as e:
                errors += e.messages
                continue
        raise ValidationError(errors)

    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
        for field in self.fields:
            try:
                value = field._serialize(value, attr, obj, **kwargs)
                return value
            except Exception:
                continue

        raise AttributeError(f"Could not serialize value for {self.__repr__()}")

    def __repr__(self) -> str:
        return f"<UnionField fields=[{', '.join(repr(field) for field in self.fields)}]>"


class APIModel(abc.ABC):
    schema: Schema


BASE_URL = "https://www.dnd5eapi.co"


class ResourceModel(APIModel, abc.ABC):
    @property
    def full_url(self) -> str:
        if hasattr(self, 'url'):
            return f"{BASE_URL}{self.url}"
        raise NotImplementedError

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> Menu:
        raise NotImplementedError
