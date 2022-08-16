from dataclasses import dataclass, field
from typing import Optional

from marshmallow import Schema, fields, post_load

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory

from .framework import APIModel, ResourceModel
from .common import StartingEquipment, APIReference, ResourceFeature, ResourceFeatureSchema, StartingEquipmentSchema
from .general import Choice, APIReferenceSchema, ChoiceSchema


# ---------- Dataclasses ----------
@dataclass
class Prerequisite(APIModel):
    minimum_score: int
    ability_score: APIReference


@dataclass
class Multiclassing(ResourceModel):
    prerequisites: Optional[list[Prerequisite]] = field(default=None)
    prerequisite_options: Optional[Choice] = field(default=None)
    proficiencies: Optional[list[APIReference]] = field(default=None)
    proficiency_choices: Optional[list[Choice]] = field(default=None)


@dataclass
class Spellcasting(ResourceModel):
    level: int
    info: list[ResourceFeature]
    spellcasting_ability: APIReference


@dataclass
class Class(ResourceModel):
    index: str
    name: str
    url: str
    hit_die: int
    class_levels: str
    multi_classing: Multiclassing
    starting_equipment: list[StartingEquipment]
    starting_equipment_options: list[Choice]
    proficiency_choices: list[Choice]
    proficiencies: list[APIReference]
    saving_throws: list[APIReference]
    subclasses: list[APIReference]

    spellcasting: Optional[Spellcasting] = field(default=None)
    spells: Optional[str] = field(default=None)

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.ClassMenu:
        return dnd_resource_menus.ClassMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


# ---------- Schemas ----------
class PrerequisiteSchema(Schema):
    minimum_score = fields.Int(required=True)
    ability_score = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Prerequisite(**data)


class MulticlassingSchema(Schema):
    prerequisites = fields.List(fields.Nested(PrerequisiteSchema()))
    prerequisite_options = fields.Nested(ChoiceSchema())
    proficiencies = fields.List(fields.Nested(APIReferenceSchema()))
    proficiency_choices = fields.List(fields.Nested(ChoiceSchema()))

    @post_load
    def make_api_model(self, data, **kwargs):
        return Multiclassing(**data)


class SpellcastingSchema(Schema):
    level = fields.Int(required=True)
    info = fields.List(fields.Nested(ResourceFeatureSchema(), required=True))
    spellcasting_ability = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Spellcasting(**data)


class ClassSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    hit_die = fields.Int(required=True)
    class_levels = fields.Str(required=True)
    multi_classing = fields.Nested(MulticlassingSchema(), required=True)
    spellcasting = fields.Nested(SpellcastingSchema())
    spells = fields.Str()
    starting_equipment = fields.List(fields.Nested(StartingEquipmentSchema()), required=True)
    starting_equipment_options = fields.List(fields.Nested(ChoiceSchema()), required=True)
    proficiency_choices = fields.List(fields.Nested(ChoiceSchema()), required=True)
    proficiencies = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    saving_throws = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    subclasses = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Class(**data)
