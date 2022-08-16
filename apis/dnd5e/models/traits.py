from dataclasses import dataclass, field
from typing import Union, Optional
from enum import Enum

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from .framework import ResourceModel, UnionField, APIModel
from .general import APIReference, APIReferenceSchema, Choice, ChoiceSchema, DC, DCSchema
from .spells import SpellAOE, SpellAOESchema, SpellDamage, SpellDamageSchema


# ---------- Enums ----------
class BreathWeaponUsageType(Enum):
    per_rest = "per rest"


# ---------- Dataclasses ----------
@dataclass
class BreathWeaponUsage(APIModel):
    times: int
    type: BreathWeaponUsageType


@dataclass
class BreathWeapon(APIModel):
    name: str
    desc: str
    area_of_effect: SpellAOE
    damage: list[SpellDamage]
    dc: DC
    usage: BreathWeaponUsage


@dataclass
class TraitSpecificBreathWeapon(APIModel):
    damage_type: APIReference
    breath_weapon: BreathWeapon


@dataclass
class TraitSpecificSubtraitOptions(APIModel):
    subtrait_options: Choice


@dataclass
class TraitSpecificSpellOptions(APIModel):
    spell_options: Choice


@dataclass
class Trait(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    races: list[APIReference]
    subraces: list[APIReference]
    proficiencies: list[APIReference]
    proficiency_choices: Optional[Choice] = field(default=None)
    language_options: Optional[Choice] = field(default=None)
    trait_specific: Optional[Union[Choice, TraitSpecificBreathWeapon]] = field(default=None)
    parent: Optional[APIReference] = field(default=None)


# ---------- Schemas ----------
class BreathWeaponUsageSchema(Schema):
    times = fields.Int(required=True)
    type = EnumField(BreathWeaponUsageType, required=True, by_value=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return BreathWeaponUsage(**data)


class BreathWeaponSchema(Schema):
    name = fields.Str(required=True)
    desc = fields.Str(required=True)
    area_of_effect = fields.Nested(SpellAOESchema(), required=True)
    damage = fields.List(fields.Nested(SpellDamageSchema()), required=True)
    dc = fields.Nested(DCSchema(), required=True)
    usage = fields.Nested(BreathWeaponUsageSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return BreathWeapon(**data)


class TraitSpecificBreathWeaponSchema(Schema):
    damage_type = fields.Nested(APIReferenceSchema(), required=True)
    breath_weapon = fields.Nested(BreathWeaponSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return TraitSpecificBreathWeapon(**data)


class TraitSpecificSubtraitOptionsSchema(Schema):
    subtrait_options = fields.Nested(ChoiceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return TraitSpecificSubtraitOptions(**data)


class TraitSpecificSpellOptionsSchema(Schema):
    spell_options = fields.Nested(ChoiceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return TraitSpecificSpellOptions(**data)


class TraitSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    races = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    subraces = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    proficiencies = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    proficiency_choices = fields.Nested(ChoiceSchema())
    language_options = fields.Nested(ChoiceSchema())
    trait_specific = UnionField(
        fields=[
            fields.Nested(ChoiceSchema()),
            fields.Nested(TraitSpecificBreathWeaponSchema()),
            fields.Nested(TraitSpecificSubtraitOptionsSchema()),
            fields.Nested(TraitSpecificSpellOptionsSchema()),
        ]
    )
    parent = fields.Nested(APIReferenceSchema())

    @post_load
    def make_api_model(self, data, **kwargs):
        return Trait(**data)
