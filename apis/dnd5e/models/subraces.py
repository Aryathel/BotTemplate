from dataclasses import dataclass, field
from typing import Optional

from marshmallow import Schema, fields, post_load

from .framework import ResourceModel
from .general import APIReference, APIReferenceSchema, AbilityBonus, AbilityBonusSchema, Choice, ChoiceSchema


# ---------- Dataclasses ----------
@dataclass
class Subrace(ResourceModel):
    index: str
    name: str
    url: str
    desc: str
    race: APIReference
    ability_bonuses: list[AbilityBonus]
    starting_proficiencies: list[APIReference]
    languages: list[APIReference]
    racial_traits: list[APIReference]
    language_options: Optional[Choice] = field(default=None)


# ---------- Schemas ----------
class SubraceSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.Str(required=True)
    race = fields.Nested(APIReferenceSchema(), required=True)
    ability_bonuses = fields.List(fields.Nested(AbilityBonusSchema()), required=True)
    starting_proficiencies = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    languages = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    language_options = fields.Nested(ChoiceSchema())
    racial_traits = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Subrace(**data)
