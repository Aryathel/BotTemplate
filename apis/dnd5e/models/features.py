from dataclasses import dataclass, field
from typing import Optional

from marshmallow import Schema, fields, post_load

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory
from .framework import ResourceModel, APIModel
from .general import APIReference, APIReferenceSchema, Choice, ChoiceSchema, OptionPrerequisiteSchema, \
    OptionPrerequisite


# ---------- Dataclasses ----------
@dataclass
class FeatureSpecific(APIModel):
    subfeature_options: Optional[Choice] = field(default=None)
    expertise_options: Optional[Choice] = field(default=None)


@dataclass
class Feature(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    level: int
    class_: APIReference
    prerequisites: list[OptionPrerequisite]
    parent: Optional[APIReference] = field(default=None)
    subclass: Optional[APIReference] = field(default=None)
    feature_specific: Optional[FeatureSpecific] = field(default=None)
    reference: Optional[str] = field(default=None)

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.FeatureMenu:
        return dnd_resource_menus.FeatureMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral,
        )


# ---------- Schemas ----------
class FeatureSpecificSchema(Schema):
    subfeature_options = fields.Nested(ChoiceSchema())
    expertise_options = fields.Nested(ChoiceSchema())

    @post_load
    def make_api_model(self, data, **kwargs):
        return FeatureSpecific(**data)


class FeatureSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    level = fields.Int(required=True)
    class_ = fields.Nested(APIReferenceSchema(), required=True, data_key='class')
    subclass = fields.Nested(APIReferenceSchema())
    feature_specific = fields.Nested(FeatureSpecificSchema())
    prerequisites = fields.List(fields.Nested(OptionPrerequisiteSchema()), required=True)
    parent = fields.Nested(APIReferenceSchema())
    reference = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return Feature(**data)
