from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union, Mapping

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from .framework import ResourceModel, APIModel, UnionField
from .general import Choice, ActionType, DC, Damage, APIReference, DCSchema, DamageSchema, ChoiceSchema, \
    APIReferenceSchema


# ---------- Enums ---------
class MonsterSize(Enum):
    tiny = "Tiny"
    small = "Small"
    medium = "Medium"
    large = "Large"
    huge = "Huge"
    gargantuan = "Gargantuan"


class MonsterAlignment(Enum):
    lawful_good = "lawful good"
    neutral_good = "neutral good"
    chaotic_good = "chaotic good"
    lawful_neutral = "lawful neutral"
    neutral = "neutral"
    chaotic_neutral = "chaotic neutral"
    lawful_evil = "lawful evil"
    neutral_evil = "neutral evil"
    chaotic_evil = "chaotic evil"
    unaligned = "unaligned"
    any_alignment = "any alignment"
    any_non_good_alignment = "any non-good alignment"
    any_non_lawful_alignment = "any non-lawful alignment"
    any_chaotic_alignment = "any chaotic alignment"
    any_evil_alignment = "any evil alignment"
    neutral_good_or_neutral_evil = "neutral good (50%) or neutral evil (50%)"


class MonsterUsageType(Enum):
    at_will = "at will"
    per_day = "per day"
    recharge_after_rest = "recharge after rest"
    recharge_on_roll = "recharge on roll"


# ---------- Dataclasses ----------
@dataclass
class MonsterUsage(APIModel):
    type: MonsterUsageType
    times: Optional[int] = field(default=None)
    rest_types: Optional[list[str]] = field(default=None)
    dice: Optional[str] = field(default=None)
    min_value: Optional[int] = field(default=None)


@dataclass
class MonsterAttack(APIModel):
    name: str
    dc: DC
    damage: Optional[Damage] = field(default=None)


@dataclass
class MonsterSubAction(APIModel):
    action_name: str
    count: Union[int, str]
    type: ActionType


@dataclass
class MonsterAction(APIModel):
    name: str
    desc: str
    actions: Optional[list[MonsterSubAction]] = field(default=None)
    multiattack_type: Optional[str] = field(default=None)
    attack_bonus: Optional[int] = field(default=None)
    dc: Optional[DC] = field(default=None)
    attacks: Optional[list[MonsterAttack]] = field(default=None)
    damage: Optional[list[Damage]] = field(default=None)
    action_options: Optional[Choice] = field(default=None)
    options: Optional[Choice] = field(default=None)
    usage: Optional[MonsterUsage] = field(default=None)


@dataclass
class MonsterLegendaryAction(MonsterAction):
    pass


@dataclass
class MonsterProficiency(APIModel):
    value: int
    proficiency: APIReference


@dataclass
class MonsterReaction(MonsterAction):
    pass


@dataclass
class MonsterSenses(APIModel):
    passive_perception: int
    blindsight: Optional[str] = field(default=None)
    darkvision: Optional[str] = field(default=None)
    tremorsense: Optional[str] = field(default=None)
    truesight: Optional[str] = field(default=None)


@dataclass
class MonsterSpell(APIModel):
    name: str
    level: int
    url: str
    usage: Optional[MonsterUsage] = field(default=None)
    notes: Optional[str] = field(default=None)


@dataclass
class MonsterSpellcasting(APIModel):
    ability: APIReference
    components_required: list[str]
    spells: list[MonsterSpell]
    dc: Optional[int] = field(default=None)
    school: Optional[str] = field(default=None)
    slots: Optional[Mapping[str, int]] = field(default=None)
    modifier: Optional[int] = field(default=None)
    level: Optional[int] = field(default=None)


@dataclass
class MonsterAbility(APIModel):
    name: str
    desc: str
    attack_bonus: Optional[int] = field(default=None)
    damage: Optional[list[Damage]] = field(default=None)
    dc: Optional[DC] = field(default=None)
    spellcasting: Optional[MonsterSpellcasting] = field(default=None)
    usage: Optional[MonsterUsage] = field(default=None)


@dataclass
class MonsterSpeed(APIModel):
    walk: Optional[str] = field(default=None)
    burrow: Optional[str] = field(default=None)
    climb: Optional[str] = field(default=None)
    fly: Optional[str] = field(default=None)
    swim: Optional[str] = field(default=None)
    hover: Optional[bool] = field(default=None)


@dataclass
class Monster(ResourceModel):
    index: str
    name: str
    url: str
    charisma: int
    constitution: int
    dexterity: int
    intelligence: int
    strength: int
    wisdom: int
    size: MonsterSize
    type: str
    armor_class: int
    hit_points: int
    hit_dice: str
    actions: list[MonsterAction]
    legendary_actions: list[MonsterLegendaryAction]
    challenge_rating: int
    condition_immunities: list[APIReference]
    damage_immunities: list[str]
    damage_resistances: list[str]
    damage_vulnerabilities: list[str]
    languages: str
    proficiencies: list[MonsterProficiency]
    senses: MonsterSenses
    special_abilities: list[MonsterAbility]
    speed: MonsterSpeed
    xp: int
    alignment: MonsterAlignment
    forms: Optional[list[APIReference]] = field(default=None)
    subtype: Optional[str] = field(default=None)
    desc: Optional[str] = field(default=None)
    reactions: Optional[list[MonsterReaction]] = field(default=None)


# ---------- Schemas ----------
class MonsterUsageSchema(Schema):
    type = EnumField(MonsterUsageType, required=True, by_value=True)
    rest_types = fields.List(fields.Str())
    times = fields.Int()
    dice = fields.Str()
    min_value = fields.Int()

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterUsage(**data)


class MonsterAttackSchema(Schema):
    name = fields.Str()
    dc = fields.Nested(DCSchema(), required=True)
    damage = fields.List(fields.Nested(DamageSchema()))

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterAttack(**data)


class MonsterSubActionSchema(Schema):
    action_name = fields.Str(required=True)
    count = UnionField(fields=[fields.Int(), fields.Str()], required=True)
    type = EnumField(ActionType, required=True, by_value=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterSubAction(**data)


class MonsterActionSchema(Schema):
    name = fields.Str(required=True)
    desc = fields.Str(required=True)
    action_options = fields.Nested(ChoiceSchema())
    actions = fields.List(fields.Nested(MonsterSubActionSchema()))
    options = fields.Nested(ChoiceSchema())
    multiattack_type = fields.Str()
    attack_bonus = fields.Int()
    dc = fields.Nested(DCSchema())
    attacks = fields.List(fields.Nested(MonsterAttackSchema()))
    damage = fields.List(UnionField(fields=[fields.Nested(DamageSchema()), fields.Nested(ChoiceSchema())]))
    usage = fields.Nested(MonsterUsageSchema())

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterAction(**data)


class MonsterLegendaryActionSchema(MonsterActionSchema):
    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterLegendaryAction(**data)


class MonsterProficiencySchema(Schema):
    value = fields.Int(required=True)
    proficiency = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterProficiency(**data)


class MonsterReactionSchema(MonsterActionSchema):
    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterReaction(**data)


class MonsterSensesSchema(Schema):
    passive_perception = fields.Int(required=True)
    blindsight = fields.Str()
    darkvision = fields.Str()
    tremorsense = fields.Str()
    truesight = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterSenses(**data)


class MonsterSpellSchema(Schema):
    name = fields.Str(required=True)
    level = fields.Int(required=True)
    url = fields.Str(required=True)
    usage = fields.Nested(MonsterUsageSchema())
    notes = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterSpell(**data)


class MonsterSpellcastingSchema(Schema):
    ability = fields.Nested(APIReferenceSchema(), required=True)
    dc = fields.Int()
    modifier = fields.Int()
    components_required = fields.List(fields.Str(), required=True)
    school = fields.Str()
    slots = fields.Mapping(fields.Str(), fields.Int())
    spells = fields.List(fields.Nested(MonsterSpellSchema()), required=True)
    level = fields.Int()

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterSpellcasting(**data)


class MonsterAbilitySchema(Schema):
    name = fields.Str(required=True)
    desc = fields.Str(required=True)
    attack_bonus = fields.Int()
    damage = fields.List(fields.Nested(DamageSchema()))
    dc = fields.Nested(DCSchema())
    spellcasting = fields.Nested(MonsterSpellcastingSchema())
    usage = fields.Nested(MonsterUsageSchema())

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterAbility(**data)


class MonsterSpeedSchema(Schema):
    walk = fields.Str()
    burrow = fields.Str()
    climb = fields.Str()
    fly = fields.Str()
    swim = fields.Str()
    hover = fields.Bool()

    @post_load
    def make_api_model(self, data, **kwargs):
        return MonsterSpeed(**data)


class MonsterSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.Str()
    charisma = fields.Int(required=True)
    constitution = fields.Int(required=True)
    dexterity = fields.Int(required=True)
    intelligence = fields.Int(required=True)
    strength = fields.Int(required=True)
    wisdom = fields.Int(required=True)
    size = EnumField(MonsterSize, required=True, by_value=True)
    type = fields.Str(required=True)
    subtype = fields.Str()
    alignment = EnumField(MonsterAlignment, required=True, by_value=True)
    armor_class = fields.Int(required=True)
    hit_points = fields.Int(required=True)
    hit_dice = fields.Str(required=True)
    actions = fields.List(fields.Nested(MonsterActionSchema()), required=True)
    legendary_actions = fields.List(fields.Nested(MonsterLegendaryActionSchema()), required=True)
    challenge_rating = fields.Int(required=True)
    condition_immunities = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    damage_immunities = fields.List(fields.Str(), required=True)
    damage_resistances = fields.List(fields.Str(), required=True)
    damage_vulnerabilities = fields.List(fields.Str(required=True))
    forms = fields.List(fields.Nested(APIReferenceSchema()))
    languages = fields.Str(required=True)
    proficiencies = fields.List(fields.Nested(MonsterProficiencySchema()), required=True)
    reactions = fields.List(fields.Nested(MonsterReactionSchema()))
    senses = fields.Nested(MonsterSensesSchema(), required=True)
    special_abilities = fields.List(fields.Nested(MonsterAbilitySchema()), required=True)
    speed = fields.Nested(MonsterSpeedSchema(), required=True)
    xp = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Monster(**data)
