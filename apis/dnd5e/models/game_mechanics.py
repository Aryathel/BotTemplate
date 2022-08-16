from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory

from .framework import ResourceModel


# ---------- Dataclasses ----------
@dataclass
class Condition(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.ConditionMenu:
        return dnd_resource_menus.ConditionMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral,
        )


@dataclass
class DamageType(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.DamageTypeMenu:
        return dnd_resource_menus.DamageTypeMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class MagicSchool(ResourceModel):
    index: str
    name: str
    url: str
    desc: str


# ---------- Schemas ----------
class ConditionSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Condition(**data)


class DamageTypeSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return DamageType(**data)


class MagicSchoolSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return MagicSchool(**data)
