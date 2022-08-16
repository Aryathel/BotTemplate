from dataclasses import dataclass
from enum import Enum

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from .framework import ResourceModel, APIModel
from .general import APIReference, APIReferenceSchema


# ---------- Enums ----------
class SubclassSpellPrerequisiteType(Enum):
    level = "level"
    feature = "feature"


# ---------- Dataclasses ----------
@dataclass
class SubclassSpellPrerequisite(APIModel):
    index: str
    name: str
    url: str
    type: SubclassSpellPrerequisiteType


@dataclass
class SubclassSpell(APIModel):
    prerequisites: list[SubclassSpellPrerequisite]
    spell: APIReference


@dataclass
class Subclass(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    class_: APIReference
    subclass_flavor: str
    subclass_levels: str
    spells: list[SubclassSpell]


# ---------- Schemas ----------
class SubclassSpellPrerequisiteSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    type = EnumField(SubclassSpellPrerequisiteType, required=True, by_value=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return SubclassSpellPrerequisite(**data)


class SubclassSpellSchema(Schema):
    prerequisites = fields.List(fields.Nested(SubclassSpellPrerequisiteSchema()), required=True)
    spell = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return SubclassSpell(**data)


class SubclassSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    class_ = fields.Nested(APIReferenceSchema(), required=True, data_key="class")
    subclass_flavor = fields.Str(required=True)
    subclass_levels = fields.Str(required=True)
    spells = fields.List(fields.Nested(SubclassSpellSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Subclass(**data)
