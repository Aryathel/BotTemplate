from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from .framework import APIModel, ResourceModel
from .general import APIReferenceSchema, APIReference


# ---------- Dataclasses ----------
@dataclass
class Prerequisite(APIModel):
    minimum_score: int
    ability_score: APIReference


@dataclass
class APIReferenceList(ResourceModel):
    count: int
    results: list[APIReference]


@dataclass
class StartingEquipment(APIModel):
    quantity: int
    equipment: APIReference


@dataclass
class ResourceFeature(APIModel):
    name: str
    desc: list[str]


# ---------- Schemas ----------
class PrerequisiteSchema(Schema):
    minimum_score = fields.Int(required=True)
    ability_score = fields.Nested(APIReferenceSchema(), required=True)


class APIReferenceListSchema(Schema):
    count = fields.Int(required=True)
    results = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return APIReferenceList(**data)


class StartingEquipmentSchema(Schema):
    quantity = fields.Int(required=True)
    equipment = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return StartingEquipment(**data)


class ResourceFeatureSchema(Schema):
    name = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ResourceFeature(**data)
