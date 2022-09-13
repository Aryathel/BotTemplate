from dataclasses import dataclass, field
from typing import Optional

from marshmallow import Schema, fields, post_load

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory

from .framework import ResourceModel
from .general import AbilityBonus, APIReference, Choice, AbilityBonusSchema, APIReferenceSchema, ChoiceSchema


# --------- Dataclasses ----------
@dataclass
class Race(ResourceModel):
    index: str
    name: str
    url: str
    speed: int
    ability_bonuses: list[AbilityBonus]
    alignment: str
    age: str
    size: str
    size_description: str
    starting_proficiencies: list[APIReference]
    languages: list[APIReference]
    language_desc: str
    traits: list[APIReference]
    subraces: list[APIReference]
    ability_bonus_options: Optional[Choice] = field(default=None)
    starting_proficiency_options: Optional[Choice] = field(default=None)
    language_options: Optional[Choice] = field(default=None)

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.RaceMenu:
        return dnd_resource_menus.RaceMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


# --------- Schemas ----------
class RaceSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    speed = fields.Int(required=True)
    ability_bonuses = fields.List(fields.Nested(AbilityBonusSchema()), required=True)
    ability_bonus_options = fields.Nested(ChoiceSchema())
    alignment = fields.Str(required=True)
    age = fields.Str(required=True)
    size = fields.Str(required=True)
    size_description = fields.Str(required=True)
    starting_proficiencies = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    starting_proficiency_options = fields.Nested(ChoiceSchema())
    languages = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    language_options = fields.Nested(ChoiceSchema())
    language_desc = fields.Str(required=True)
    traits = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    subraces = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Race(**data)
