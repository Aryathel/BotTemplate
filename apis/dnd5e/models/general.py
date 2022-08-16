import abc
from enum import Enum
from dataclasses import dataclass, field
from typing import Union, TypeVar, Optional, TYPE_CHECKING

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField
from marshmallow_oneofschema import OneOfSchema

from .framework import APIModel

if TYPE_CHECKING:
    from templates import Interaction


# Option typing
OptionReferenceT = TypeVar('OptionReferenceT', bound='OptionReference')
OptionActionT = TypeVar('OptionActionT', bound='OptionAction')
OptionMultipleT = TypeVar('OptionMultipleT', bound='OptionMultiple')
OptionChoiceT = TypeVar('OptionChoiceT', bound='OptionChoice')
OptionStringT = TypeVar('OptionStringT', bound='OptionString')
OptionIdealT = TypeVar('OptionIdealT', bound='OptionIdeal')
OptionCountedReferenceT = TypeVar('OptionCountedReferenceT', bound='OptionCountedReference')
OptionScorePrerequisiteT = TypeVar('OptionScorePrerequisiteT', bound='OptionScorePrerequisite')
AbilityBonusT = TypeVar('AbilityBonusT', bound='AbilityBonus')
OptionBreathT = TypeVar('OptionBreathT', bound='OptionBreath')
OptionDamageT = TypeVar('OptionDamageT', bound='OptionDamage')
OptionT = Union[
    OptionReferenceT, OptionActionT, OptionMultipleT, OptionChoiceT, OptionStringT,
    OptionIdealT, OptionCountedReferenceT, OptionScorePrerequisiteT, AbilityBonusT,
    OptionBreathT, OptionDamageT
]


# OptionSet typing
OptionSetOptionsArrayT = TypeVar('OptionSetOptionsArrayT', bound='OptionSetOptionsArray')
OptionSetEquipmentCategoryT = TypeVar('OptionSetEquipmentCategoryT', bound='OptionSetEquipmentCategory')
OptionSetResourceListT = TypeVar('OptionSetResourceListT', bound='OptionSetResourceList')
OptionSetT = Union[OptionSetOptionsArrayT, OptionSetEquipmentCategoryT, OptionSetResourceListT]


# ---------- Enums ----------
class DCSuccessType(Enum):
    none_ = "none"
    half = "half"
    other = "other"


class OptionType(Enum):
    reference = "reference"
    action = "action"
    multiple = "multiple"
    choice = "choice"
    string = "string"
    ideal = "ideal"
    counted_reference = "counted_reference"
    score_prerequisite = "score_prerequisite"
    ability_bonus = "ability_bonus"
    breath = "breath"
    damage = "damage"


class ActionType(Enum):
    melee = "melee"
    ranged = "ranged"
    ability = "ability"
    magic = "magic"


class OptionSetType(Enum):
    options_array = "options_array"
    equipment_category = "equipment_category"
    resource_list = "resource_list"


class OptionPrerequisiteType(Enum):
    proficiency = "proficiency"
    spell = "Spell"
    level = "level"
    feature = "feature"


# ---------- Classes ----------
@dataclass
class APIReference(APIModel):
    index: str
    name: str
    url: str


@dataclass
class DC(APIModel):
    dc_type: APIReference
    success_type: DCSuccessType
    dc_value: Optional[int] = field(default=None)


@dataclass
class Damage(APIModel):
    damage_type: APIReference
    damage_dice: str
    dc: Optional[DC] = field(default=None)


@dataclass
class OptionPrerequisite(APIModel):
    type: OptionPrerequisiteType
    proficiency: Optional[APIReference] = field(default=None)
    spell: Optional[str] = field(default=None)
    level: Optional[int] = field(default=None)
    feature: Optional[str] = field(default=None)


class Option(APIModel, abc.ABC):
    def to_str(self, interaction: 'Interaction') -> str:
        raise NotImplementedError


@dataclass
class OptionReference(Option):
    item: APIReference

    def to_str(self, interaction: 'Interaction') -> str:
        return self.item.name


@dataclass
class OptionAction(Option):
    action_name: str
    count: int
    type: ActionType
    desc: Optional[str] = field(default=None)


@dataclass
class OptionMultiple(Option):
    items_: list[OptionT]
    desc: Optional[str] = field(default=None)


@dataclass
class OptionChoice(Option):
    choice: 'Choice'

    async def to_str(self, interaction: 'Interaction') -> str:
        if self.choice.type == 'equipment':
            if self.choice.from_.option_set_type == 'equipment_category':
                choices = await interaction.client.dnd_client.lookup(
                    (self.choice.from_.equipment_category, 'equipment-categories')
                )
                return f"Choose {self.choice.choose} from {self.choice.from_}"
        raise NotImplementedError


@dataclass
class OptionIdeal(Option):
    desc: str
    alignments: list[APIReference]


@dataclass
class OptionString(Option):
    string: str


@dataclass
class OptionCountedReference(Option):
    count: int
    of: APIReference
    prerequisites: Optional[list[OptionPrerequisite]] = field(default=None)

    def to_str(self) -> str:
        return f"{self.of.name} x{self.count}"


@dataclass
class OptionScorePrerequisite(Option):
    ability_score: APIReference
    minimum_score: int


@dataclass
class AbilityBonus(Option):
    ability_score: APIReference
    bonus: int


@dataclass
class OptionBreath(Option):
    name: str
    dc: DC
    damage: Optional[list[Damage]] = field(default=None)


@dataclass
class OptionDamage(Option):
    damage_type: APIReference
    damage_dice: str
    notes: Optional[str] = field(default=None)


class OptionSet(APIModel):
    pass


@dataclass
class OptionSetOptionsArray(OptionSet):
    options: list[OptionT]


@dataclass
class OptionSetEquipmentCategory(OptionSet):
    equipment_category: APIReference


@dataclass
class OptionSetResourceList(OptionSet):
    resource_list_url: str


@dataclass
class Choice(APIModel):
    choose: int
    type: str
    from_: OptionSetT
    desc: Optional[str] = field(default=None)


# ---------- Schemas ----------
class APIReferenceSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return APIReference(**data)


class DCSchema(Schema):
    dc_type = fields.Nested(APIReferenceSchema(), required=True)
    dc_value = fields.Int()
    success_type = EnumField(DCSuccessType, required=True, by_value=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return DC(**data)


class DamageSchema(Schema):
    damage_type = fields.Nested(APIReferenceSchema(), required=True)
    damage_dice = fields.Str(required=True)
    dc = fields.Nested(DCSchema())

    @post_load
    def make_api_model(self, data, **kwargs):
        return Damage(**data)


class OptionPrerequisiteSchema(Schema):
    type = EnumField(OptionPrerequisiteType, required=True, by_value=True)

    # proficiency
    proficiency = fields.Nested(APIReferenceSchema())

    # spell
    spell = fields.Str()

    # level
    level = fields.Int()

    # feature
    feature = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionPrerequisite(**data)


class OptionReferenceSchema(Schema):
    item = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionReference(**data)


class OptionActionSchema(Schema):
    action_name = fields.Str(required=True)
    count = fields.Int(required=True)
    type = EnumField(ActionType, required=True)
    desc = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionAction(**data)


class OptionMultipleSchema(Schema):
    # Renamed to avoid an error with accessing the dict.items() method
    # during serialization
    items_ = fields.List(fields.Nested(lambda: OptionSchema), data_key='items', required=True)
    desc = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionMultiple(**data)


class OptionChoiceSchema(Schema):
    choice = fields.Nested(lambda: ChoiceSchema, required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionChoice(**data)


class OptionStringSchema(Schema):
    string = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionString(**data)


class OptionIdealSchema(Schema):
    desc = fields.Str(required=True)
    alignments = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionIdeal(**data)


class OptionCountedReferenceSchema(Schema):
    count = fields.Int(required=True)
    of = fields.Nested(APIReferenceSchema(), required=True)
    prerequisites = fields.List(fields.Nested(OptionPrerequisiteSchema()))

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionCountedReference(**data)


class OptionScorePrerequisiteSchema(Schema):
    ability_score = fields.Nested(APIReferenceSchema(), required=True)
    minimum_score = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionScorePrerequisite(**data)


class AbilityBonusSchema(Schema):
    ability_score = fields.Nested(APIReferenceSchema(), required=True)
    bonus = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return AbilityBonus(**data)


class OptionBreathSchema(Schema):
    name = fields.Str(required=True)
    dc = fields.Nested(DCSchema(), required=True)
    damage = fields.List(fields.Nested(DamageSchema()))

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionBreath(**data)


class OptionDamageSchema(Schema):
    damage_type = fields.Nested(APIReferenceSchema(), required=True)
    damage_dice = fields.Str(required=True)
    notes = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionDamage(**data)


class OptionSchema(OneOfSchema):
    type_field = "option_type"
    type_schemas = {
        OptionType.reference.value: OptionReferenceSchema,
        OptionType.action.value: OptionActionSchema,
        OptionType.multiple.value: OptionMultipleSchema,
        OptionType.choice.value: OptionChoiceSchema,
        OptionType.string.value: OptionStringSchema,
        OptionType.ideal.value: OptionIdealSchema,
        OptionType.counted_reference.value: OptionCountedReferenceSchema,
        OptionType.score_prerequisite.value: OptionScorePrerequisiteSchema,
        OptionType.ability_bonus.value: AbilityBonusSchema,
        OptionType.breath.value: OptionBreathSchema,
        OptionType.damage.value: OptionDamageSchema,
    }

    def get_obj_type(self, obj):
        if isinstance(obj, OptionReference):
            return OptionType.reference.value
        elif isinstance(obj, OptionAction):
            return OptionType.action.value
        elif isinstance(obj, OptionMultiple):
            return OptionType.multiple.value
        elif isinstance(obj, OptionChoice):
            return OptionType.choice.value
        elif isinstance(obj, OptionString):
            return OptionType.string.value
        elif isinstance(obj, OptionIdeal):
            return OptionType.ideal.value
        elif isinstance(obj, OptionCountedReference):
            return OptionType.counted_reference.value
        elif isinstance(obj, OptionScorePrerequisite):
            return OptionType.score_prerequisite.value
        elif isinstance(obj, AbilityBonus):
            return OptionType.ability_bonus.value
        elif isinstance(obj, OptionBreath):
            return OptionType.breath.value
        elif isinstance(obj, OptionDamage):
            return OptionType.damage.value
        else:
            raise TypeError(f"Unknown object type: {obj.__class__.__name__}")


class OptionSetOptionsArraySchema(Schema):
    options = fields.List(fields.Nested(OptionSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionSetOptionsArray(**data)


class OptionSetEquipmentCategorySchema(Schema):
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionSetEquipmentCategory(**data)


class OptionSetResourceListSchema(Schema):
    resource_list_url = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return OptionSetResourceList(**data)


class OptionSetSchema(OneOfSchema):
    type_field = "option_set_type"
    type_schemas = {
        OptionSetType.options_array.value: OptionSetOptionsArraySchema,
        OptionSetType.equipment_category.value: OptionSetEquipmentCategorySchema,
        OptionSetType.resource_list.value: OptionSetResourceListSchema
    }

    def get_obj_type(self, obj):
        if isinstance(obj, OptionSetOptionsArray):
            return OptionSetType.options_array.value
        elif isinstance(obj, OptionSetEquipmentCategory):
            return OptionSetType.equipment_category.value
        elif isinstance(obj, OptionSetResourceList):
            return OptionSetType.resource_list.value
        else:
            raise TypeError(f"Unknown object type: {obj.__class__.__name__}")


class ChoiceSchema(Schema):
    desc = fields.Str()
    choose = fields.Int(required=True)
    type = fields.Str(required=True)
    from_ = fields.Nested(OptionSetSchema(), data_key="from", required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Choice(**data)
