from dataclasses import dataclass
from enum import Enum

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory
from . import APIReferenceList
from .framework import ResourceModel, APIModel
from .general import APIReference, APIReferenceSchema


# ---------- Enums ----------
from .subclass_levels import SubclassLevel


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

    @property
    def embed_format(self) -> str:
        return f'{self.type.name.title()}: {self.name}'


@dataclass
class SubclassSpell(APIModel):
    prerequisites: list[SubclassSpellPrerequisite]
    spell: APIReference

    @property
    def embed_format(self) -> str:
        res = f'`{self.spell.name}`: '
        if self.prerequisites:
            res += '\n> *Prerequisites: ' + ', '.join(f'`{p.embed_format}`' for p in self.prerequisites) + '*'
        return res


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

    async def subclass_features_list(self, interaction: 'Interaction') -> APIReferenceList:
        return await interaction.client.dnd_client.lookup_raw(
            self.url + '/features',
            interaction.client.dnd_client.api_ref_list_schema,
        )

    async def subclass_levels_list(self, interaction: 'Interaction') -> list[SubclassLevel]:
        return await interaction.client.dnd_client.lookup_raw(
            self.subclass_levels,
            interaction.client.dnd_client.subclass_level_schema,
            is_list=True
        )

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.SubclassMenu:
        return dnd_resource_menus.SubclassMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


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
