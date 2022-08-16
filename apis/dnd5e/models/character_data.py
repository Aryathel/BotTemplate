from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory

from .common import StartingEquipment, ResourceFeature, StartingEquipmentSchema, ResourceFeatureSchema
from .equipment import EquipmentCategory
from .general import APIReference, APIReferenceSchema, Choice, ChoiceSchema
from .framework import ResourceModel


# ---------- Enums ----------
class LanguageType(Enum):
    standard = "Standard"
    exotic = "Exotic"


# ---------- Dataclasses ----------
@dataclass
class AbilityScore(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    full_name: str
    skills: list[APIReference]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.AbilityScoreMenu:
        return dnd_resource_menus.AbilityScoreMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class Alignment(ResourceModel):
    index: str
    name: str
    url: str
    desc: str
    abbreviation: str

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.AlignmentMenu:
        return dnd_resource_menus.AlignmentMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class Background(ResourceModel):
    index: str
    name: str
    url: str
    starting_proficiencies: list[APIReference]
    starting_equipment: list[StartingEquipment]
    starting_equipment_options: list[Choice]
    language_options: Choice
    feature: ResourceFeature
    personality_traits: Choice
    ideals: Choice
    bonds: Choice
    flaws: Choice

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.BackgroundMenu:
        return dnd_resource_menus.BackgroundMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class Language(ResourceModel):
    index: str
    name: str
    url: str
    type: LanguageType
    typical_speakers: list[str]
    script: Optional[str] = field(default=None)
    desc: Optional[str] = field(default=None)


@dataclass
class Proficiency(ResourceModel):
    index: str
    name: str
    url: str
    type: str
    classes: list[APIReference]
    races: list[APIReference]
    reference: APIReference


@dataclass
class Skill(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    ability_score: APIReference


# ---------- Schemas ----------
class AbilityScoreSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    full_name = fields.Str(required=True)
    skills = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return AbilityScore(**data)


class AlignmentSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.Str(required=True)
    abbreviation = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Alignment(**data)


class BackgroundSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    starting_proficiencies = fields.List(fields.Nested(APIReferenceSchema(), required=True))
    starting_equipment = fields.List(fields.Nested(StartingEquipmentSchema(), required=True))
    starting_equipment_options = fields.List(fields.Nested(ChoiceSchema(), required=True))
    language_options = fields.Nested(ChoiceSchema(), required=True)
    feature = fields.Nested(ResourceFeatureSchema(), required=True)
    personality_traits = fields.Nested(ChoiceSchema(), required=True)
    ideals = fields.Nested(ChoiceSchema(), required=True)
    bonds = fields.Nested(ChoiceSchema(), required=True)
    flaws = fields.Nested(ChoiceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Background(**data)


class LanguageSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    type = EnumField(LanguageType, required=True, by_value=True)
    script = fields.Str()
    typical_speakers = fields.List(fields.Str(), required=True)
    desc = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return Language(**data)


class ProficiencySchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    type = fields.Str(required=True)
    classes = fields.List(fields.Nested(APIReferenceSchema(), required=True))
    races = fields.List(fields.Nested(APIReferenceSchema(), required=True))
    reference = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Proficiency(**data)


class SkillSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    ability_score = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Skill(**data)
