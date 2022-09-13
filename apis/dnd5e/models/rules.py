from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory
from .framework import ResourceModel
from .general import APIReference, APIReferenceSchema


# ---------- Dataclasses ----------
@dataclass
class RuleSection(ResourceModel):
    index: str
    name: str
    url: str
    desc: str

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.RuleSectionMenu:
        return dnd_resource_menus.RuleSectionMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class Rule(ResourceModel):
    index: str
    name: str
    url: str
    desc: str
    subsections: list[APIReference]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.RuleMenu:
        return dnd_resource_menus.RuleMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


# ---------- Schemas ----------
class RuleSectionSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return RuleSection(**data)


class RuleSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.Str(required=True)
    subsections = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Rule(**data)
