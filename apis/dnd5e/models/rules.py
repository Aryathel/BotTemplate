from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from .framework import ResourceModel
from .general import APIReference, APIReferenceSchema


# ---------- Dataclasses ----------
@dataclass
class RuleSection(ResourceModel):
    index: str
    name: str
    url: str
    desc: str


@dataclass
class Rule(ResourceModel):
    index: str
    name: str
    url: str
    desc: str
    subsections: list[APIReference]


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
