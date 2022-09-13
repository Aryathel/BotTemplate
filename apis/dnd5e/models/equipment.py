from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from templates import Interaction
from templates.views import dnd_resource_menus
from utils import EmbedFactory

from .framework import ResourceModel, APIModel
from .general import APIReference, Damage, APIReferenceSchema, DamageSchema


# ---------- Enums ----------
class RarityName(Enum):
    common = "Common"
    uncommon = "Uncommon"
    rare = "Rare"
    very_rare = "Very Rare"
    legendary = "Legendary"
    artifact = "Artifact"
    varies = "Varies"


# ---------- Dataclasses ----------
@dataclass
class ContentItem(APIModel):
    quantity: int
    item: APIReference


@dataclass
class Cost(APIModel):
    quantity: int
    unit: str

    @property
    def embed_format(self) -> str:
        return f"{self.quantity} {self.unit}"


@dataclass
class WeaponRange(APIModel):
    normal: int
    long: Optional[int] = field(default=None)

    @property
    def embed_format(self) -> str:
        res = f"`Normal: {self.normal}`"
        if self.long:
            res += f'\n`Long: {self.long}`'
        return res


@dataclass
class WeaponThrowRange(APIModel):
    normal: int
    long: int

    @property
    def embed_format(self) -> str:
        return f'`Normal: {self.normal}`\n`Long: {self.long}`'


@dataclass
class Weapon(ResourceModel):
    index: str
    name: str
    url: str
    special: list[str]
    contents: list[ContentItem]
    desc: list[str]
    equipment_category: APIReference
    weapon_category: str
    weapon_range: str
    category_range: str
    range: WeaponRange
    properties: list[APIReference]
    cost: Cost
    weight: str
    damage: Optional[Damage] = field(default=None)
    two_handed_damage: Optional[Damage] = field(default=None)
    throw_range: Optional[WeaponThrowRange] = field(default=None)

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.WeaponMenu:
        return dnd_resource_menus.WeaponMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


@dataclass
class ArmorClass(APIModel):
    base: int
    dex_bonus: bool
    max_bonus: Optional[int] = field(default=None)

    @property
    def embed_format(self) -> str:
        res = f"{self.base}"
        if self.dex_bonus:
            res += ' +DEX'
        if self.max_bonus:
            res += f' (max +{self.max_bonus})'
        return res


@dataclass
class Armor(ResourceModel):
    index: str
    name: str
    url: str
    special: list[str]
    contents: list[ContentItem]
    desc: list[str]
    equipment_category: APIReference
    armor_category: str
    armor_class: ArmorClass
    str_minimum: int
    stealth_disadvantage: bool
    properties: list[APIReference]
    cost: Cost
    weight: int

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.ArmorMenu:
        return dnd_resource_menus.ArmorMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


@dataclass
class Gear(ResourceModel):
    index: str
    name: str
    url: str
    special: list[str]
    contents: list[ContentItem]
    desc: list[str]
    equipment_category: APIReference
    gear_category: APIReference
    properties: list[APIReference]
    cost: Cost
    weight: int
    quantity: Optional[int] = field(default=None)

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.GearMenu:
        return dnd_resource_menus.GearMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class EquipmentPack(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    equipment_category: APIReference
    gear_category: APIReference
    cost: Cost
    special: list[str]
    contents: list[ContentItem]
    properties: list[APIReference]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.EquipmentPackMenu:
        return dnd_resource_menus.EquipmentPackMenu(
            resource=self,
            embed_factory=factory,
            interaction=interaction,
            ephemeral=ephemeral
        )


@dataclass
class Tool(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    equipment_category: APIReference
    tool_category: str
    cost: Cost
    weight: int
    special: list[str]
    contents: list[ContentItem]
    properties: list[APIReference]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.ToolMenu:
        return dnd_resource_menus.ToolMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


@dataclass
class VehicleSpeed(APIModel):
    quantity: int
    unit: str

    @property
    def embed_format(self) -> str:
        return f'{self.quantity} {self.unit}'


@dataclass
class Vehicle(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    equipment_category: APIReference
    vehicle_category: str
    cost: Cost
    special: list[str]
    contents: list[ContentItem]
    properties: list[APIReference]
    speed: Optional[VehicleSpeed] = field(default=None)
    capacity: Optional[str] = field(default=None)
    weight: Optional[int] = field(default=None)

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.VehicleMenu:
        return dnd_resource_menus.VehicleMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


@dataclass
class EquipmentCategory(ResourceModel):
    index: str
    name: str
    url: str
    equipment: list[APIReference]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.EquipmentCategoryMenu:
        return dnd_resource_menus.EquipmentCategoryMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


@dataclass
class Rarity(APIModel):
    name: RarityName


@dataclass
class MagicItem(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]
    equipment_category: APIReference
    rarity: Rarity
    variants: list[APIReference]
    variant: bool

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.MagicItemMenu:
        return dnd_resource_menus.MagicItemMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


@dataclass
class WeaponProperty(ResourceModel):
    index: str
    name: str
    url: str
    desc: list[str]

    def to_menu(
            self,
            interaction: Interaction,
            factory: EmbedFactory,
            ephemeral: bool = False
    ) -> dnd_resource_menus.WeaponPropertyMenu:
        return dnd_resource_menus.WeaponPropertyMenu(
            resource=self,
            interaction=interaction,
            embed_factory=factory,
            ephemeral=ephemeral
        )


# ---------- Schemas ----------
class ContentItemSchema(Schema):
    quantity = fields.Int(required=True)
    item = fields.Nested(APIReferenceSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ContentItem(**data)


class CostSchema(Schema):
    quantity = fields.Int(required=True)
    unit = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Cost(**data)


class WeaponRangeSchema(Schema):
    normal = fields.Int(required=True)
    long = fields.Int()

    @post_load
    def make_api_model(self, data, **kwargs):
        return WeaponRange(**data)


class WeaponThrowRangeSchema(Schema):
    normal = fields.Int(required=True)
    long = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return WeaponThrowRange(**data)


class WeaponSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    special = fields.List(fields.Str(), required=True)
    contents = fields.List(fields.Nested(ContentItemSchema()), required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    weapon_category = fields.Str(required=True)
    weapon_range = fields.Str(required=True)
    category_range = fields.Str(required=True)
    range = fields.Nested(WeaponRangeSchema(), required=True)
    throw_range = fields.Nested(WeaponThrowRangeSchema())
    damage = fields.Nested(DamageSchema())
    two_handed_damage = fields.Nested(DamageSchema())
    properties = fields.List(fields.Nested(APIReferenceSchema(), required=True))
    cost = fields.Nested(CostSchema(), required=True)
    weight = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Weapon(**data)


class ArmorClassSchema(Schema):
    base = fields.Int(required=True)
    dex_bonus = fields.Bool(required=True)
    max_bonus = fields.Int()

    @post_load
    def make_api_model(self, data, **kwargs):
        return ArmorClass(**data)


class ArmorSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    special = fields.List(fields.Str(), required=True)
    contents = fields.List(fields.Nested(ContentItemSchema()), required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    armor_category = fields.Str(required=True)
    armor_class = fields.Nested(ArmorClassSchema(), required=True)
    str_minimum = fields.Int(required=True)
    stealth_disadvantage = fields.Bool(required=True)
    properties = fields.List(fields.Nested(APIReferenceSchema(), required=True))
    cost = fields.Nested(CostSchema(), required=True)
    weight = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Armor(**data)


class GearSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    special = fields.List(fields.Str(), required=True)
    contents = fields.List(fields.Nested(ContentItemSchema()), required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    gear_category = fields.Nested(APIReferenceSchema(), required=True)
    properties = fields.List(fields.Nested(APIReferenceSchema(), required=True))
    cost = fields.Nested(CostSchema(), required=True)
    quantity = fields.Int()
    weight = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Gear(**data)


class EquipmentPackSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    gear_category = fields.Nested(APIReferenceSchema(), required=True)
    cost = fields.Nested(CostSchema(), required=True)
    special = fields.List(fields.Str(), required=True)
    contents = fields.List(fields.Nested(ContentItemSchema()), required=True)
    properties = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return EquipmentPack(**data)


class ToolSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    tool_category = fields.Str(required=True)
    cost = fields.Nested(CostSchema(), required=True)
    weight = fields.Int(required=True)
    special = fields.List(fields.Str(), required=True)
    contents = fields.List(fields.Nested(ContentItemSchema()), required=True)
    properties = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Tool(**data)


class VehicleSpeedSchema(Schema):
    quantity = fields.Int(required=True)
    unit = fields.Str(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return VehicleSpeed(**data)


class VehicleSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    vehicle_category = fields.Str(required=True)
    cost = fields.Nested(CostSchema(), required=True)
    weight = fields.Int()
    special = fields.List(fields.Str(), required=True)
    contents = fields.List(fields.Nested(ContentItemSchema()), required=True)
    properties = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    speed = fields.Nested(VehicleSpeedSchema())
    capacity = fields.Str()

    @post_load
    def make_api_model(self, data, **kwargs):
        return Vehicle(**data)


class EquipmentCategorySchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    equipment = fields.List(fields.Nested(APIReferenceSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return EquipmentCategory(**data)


class RaritySchema(Schema):
    name = EnumField(RarityName, required=True, by_value=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return Rarity(**data)


class MagicItemSchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)
    equipment_category = fields.Nested(APIReferenceSchema(), required=True)
    rarity = fields.Nested(RaritySchema(), required=True)
    variants = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    variant = fields.Bool(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return MagicItem(**data)


class WeaponPropertySchema(Schema):
    index = fields.Str(required=True)
    name = fields.Str(required=True)
    url = fields.Str(required=True)
    desc = fields.List(fields.Str(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return WeaponProperty(**data)
