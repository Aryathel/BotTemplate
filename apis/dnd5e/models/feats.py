from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory
from .framework import ResourceModel
from .common import Prerequisite, PrerequisiteSchema


# ---------- Dataclasses ----------
@dataclass
class Feat(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    prerequisites: list[Prerequisite]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.FeatMenu:
        return dnd_resource_menus.FeatMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral,
        )


# ---------- Schema ----------
class FeatSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    prerequisites = fields.List(fields.Nested(PrerequisiteSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Feat(**data)
