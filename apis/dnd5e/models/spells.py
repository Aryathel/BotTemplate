from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Mapping

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from .framework import ResourceModel, APIModel
from .general import APIReference, APIReferenceSchema, DCSuccessType


# ---------- Enums ----------
class ComponentType(Enum):
    verbal = "V"
    somatic = "S"
    material = "M"


class SpellAOEType(Enum):
    sphere = "sphere"
    cone = "cone"
    cylinder = "cylinder"
    line = "line"
    cube = "cube"


# ---------- Dataclasses ----------
@dataclass
class SpellAOE(APIModel):
    size: int
    type: SpellAOEType


@dataclass
class SpellDamage(APIModel):
    damage_type: Optional[APIReference] = field(default=None)
    damage_at_slot_level: Optional[Mapping[str, str]] = field(default=None)
    damage_at_character_level: Optional[Mapping[str, str]] = field(default=None)


@dataclass
class SpellDC(APIModel):
    dc_type: APIReference
    dc_success: DCSuccessType
    desc: Optional[str] = field(default=None)


@dataclass
class Spell(ResourceModel):
    id: str
    index: str
    name: str
    url: str
    desc: list[str]
    higher_level: list[str]
    range: str
    components: list[ComponentType]
    ritual: bool
    duration: str
    concentration: bool
    casting_time: str
    level: int
    school: APIReference
    classes: list[APIReference]
    subclasses: list[APIReference]
    heal_at_slot_level: Optional[Mapping[str, str]] = field(default=None)
    damage: Optional[SpellDamage] = field(default=None)
    material: Optional[str] = field(default=None)
    dc: Optional[SpellDC] = field(default=None)
    attack_type: Optional[str] = field(default=None)
    area_of_effect: Optional[SpellAOE] = field(default=None)


# ---------- Schemas ----------
class SpellAOESchema(Schema):
    size = fields.Int(required=True)
    type = EnumField(SpellAOEType, required=True, by_value=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return SpellAOE(**data)


class SpellDamageSchema(Schema):
    damage_at_character_level = fields.Mapping(fields.Str(), fields.Str())
    damage_at_slot_level = fields.Mapping(fields.Str(), fields.Str())
    damage_type = fields.Nested(APIReferenceSchema())

    @post_load
    def make_api_model(self, data, **kwargs):
        return SpellDamage(**data)


class SpellDCSchema(Schema):
    dc_type = fields.Nested(APIReferenceSchema(), required=True)
    dc_success = EnumField(DCSuccessType, required=True, by_value=True)
    desc = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return SpellDC(**data)


class SpellSchema(Schema):
    id = fields.Str(required=True, data_key="_id")
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    higher_level = fields.List(fields.Str(), required=True)
    range = fields.Str(required=True)
    components = fields.List(EnumField(ComponentType, by_value=True), required=True)
    material = fields.Str()
    area_of_effect = fields.Nested(SpellAOESchema())
    ritual = fields.Bool(required=True)
    duration = fields.Str(required=True)
    concentration = fields.Bool(required=True)
    casting_time = fields.Str(required=True)
    level = fields.Int(required=True)
    attack_type = fields.Str()
    damage = fields.Nested(SpellDamageSchema())
    school = fields.Nested(APIReferenceSchema(), required=True)
    classes = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    subclasses = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    dc = fields.Nested(SpellDCSchema())
    heal_at_slot_level = fields.Mapping(fields.Str(), fields.Str())

    @post_load
    def make_api_model(self, data, **kwargs):
        return Spell(**data)
