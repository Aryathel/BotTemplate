from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

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
