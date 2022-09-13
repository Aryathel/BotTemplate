from dataclasses import dataclass, field
from typing import Optional, Mapping, Union

from marshmallow import Schema, fields, post_load

from .framework import ResourceModel, APIModel, UnionField
from .general import APIReference, APIReferenceSchema


# ---------- Dataclasses ----------
@dataclass
class ClassLevelSpellcasting(APIModel):
    spell_slots_level_1: int
    spell_slots_level_2: int
    spell_slots_level_3: int
    spell_slots_level_4: int
    spell_slots_level_5: int
    cantrips_known: Optional[int] = field(default=None)
    spell_slots_level_6: Optional[int] = field(default=None)
    spell_slots_level_7: Optional[int] = field(default=None)
    spell_slots_level_8: Optional[int] = field(default=None)
    spell_slots_level_9: Optional[int] = field(default=None)
    spells_known: Optional[int] = field(default=None)

    @property
    def spell_slots(self) -> Mapping[int, int]:
        return {
            1: self.spell_slots_level_1,
            2: self.spell_slots_level_2,
            3: self.spell_slots_level_3,
            4: self.spell_slots_level_4,
            5: self.spell_slots_level_5,
            6: self.spell_slots_level_6,
            7: self.spell_slots_level_7,
            8: self.spell_slots_level_8,
            9: self.spell_slots_level_9,
        }

    @property
    def embed_format(self) -> str:
        entries = []
        if self.cantrips_known:
            entries.append(f"Cantrips Known: `{self.cantrips_known}`")
        if self.spells_known:
            entries.append(f"Spells Known: `{self.spells_known}`")
        for level, slots in self.spell_slots.items():
            if slots is not None:
                entries.append(f"Level {level} Spell Slots: `{slots}`")

        return '\n'.join(entries)


@dataclass
class ClassSpecificBarbarian(APIModel):
    rage_count: int
    rage_damage_bonus: int
    brutal_critical_dice: int

    @property
    def embed_format(self) -> str:
        return f"Rage Count: `{self.rage_count}`\n" \
               f"Rage Damage Bonus: `{self.rage_damage_bonus}`\n" \
               f"Brutal Critical Dice: `{self.brutal_critical_dice}`"


@dataclass
class ClassSpecificBard(APIModel):
    bardic_inspiration_die: int
    song_of_rest_die: int
    magical_secrets_max_5: int
    magical_secrets_max_7: int
    magical_secrets_max_9: int

    @property
    def embed_format(self) -> str:
        return f"Bardic Inspiration Dice: `{self.bardic_inspiration_die}`\n" \
               f"Song of Rest Dice: `{self.song_of_rest_die}`\n" \
               f"Magical Secrets:\n" \
               f"> Max Level 5: `{self.magical_secrets_max_5}`\n" \
               f"> Max Level 7: `{self.magical_secrets_max_7}`\n" \
               f"> Max Level 9: `{self.magical_secrets_max_9}`"


@dataclass
class ClassSpecificCleric(APIModel):
    channel_divinity_charges: int
    destroy_undead_cr: float

    @property
    def embed_format(self) -> str:
        return f"Channel Divinity Charges: `{self.channel_divinity_charges}`\n" \
               f"Destroy Undead Combat Rating: `{self.destroy_undead_cr}`"


@dataclass
class ClassSpecificDruid(APIModel):
    wild_shape_max_cr: float
    wild_shape_swim: bool
    wild_shape_fly: bool

    @property
    def embed_format(self) -> str:
        return f"Wild Shape Max Combat Rating: `{self.wild_shape_max_cr}`\n" \
               f"Wild Shape Can Swim: `{self.wild_shape_swim}`\n" \
               f"Wild Shape Can File: `{self.wild_shape_fly}`"


@dataclass
class ClassSpecificFighter(APIModel):
    action_surges: int
    indomitable_uses: int
    extra_attacks: int

    @property
    def embed_format(self) -> str:
        return f"Action Surge Uses: `{self.action_surges}`\n" \
               f"Indomitable Uses: `{self.indomitable_uses}`\n" \
               f"Extra Attacks: `{self.extra_attacks}`"


@dataclass
class ClassSpecificMonkMartialArts(APIModel):
    dice_count: int
    dice_value: int

    @property
    def embed_format(self) -> str:
        return f"{self.dice_count}d{self.dice_value}"


@dataclass
class ClassSpecificMonk(APIModel):
    ki_points: int
    unarmored_movement: int
    martial_arts: ClassSpecificMonkMartialArts

    @property
    def embed_format(self) -> str:
        return f"Ki Points: `{self.ki_points}`\n" \
               f"Unarmored Movement: `{self.unarmored_movement}`\n" \
               f"Martial Arts: `{self.martial_arts.embed_format}`"


@dataclass
class ClassSpecificPaladin(APIModel):
    aura_range: int

    @property
    def embed_format(self) -> str:
        return f"Aura Range: `{self.aura_range}`"


@dataclass
class ClassSpecificRanger(APIModel):
    favored_enemies: int
    favored_terrain: int

    @property
    def embed_format(self) -> str:
        return f"Favored Enemies: `{self.favored_enemies}`\n" \
               f"Favored Terrain: `{self.favored_terrain}`"


@dataclass
class ClassSpecificRogueSneakAttack(APIModel):
    dice_count: int
    dice_value: int

    @property
    def embed_format(self) -> str:
        return f"{self.dice_count}d{self.dice_value}"


@dataclass
class ClassSpecificRogue(APIModel):
    sneak_attack: ClassSpecificRogueSneakAttack

    @property
    def embed_format(self) -> str:
        return f"Sneak Attack: `{self.sneak_attack.embed_format}`"


@dataclass
class ClassSpecificSorcererCreatingSpellSlots(APIModel):
    spell_slot_level: int
    sorcery_point_cost: int

    @property
    def embed_format(self) -> str:
        return f"Level {self.spell_slot_level} Slot: `{self.sorcery_point_cost} Sorcery Points`"


@dataclass
class ClassSpecificSorcerer(APIModel):
    sorcery_points: int
    metamagic_known: int
    creating_spell_slots: list[ClassSpecificSorcererCreatingSpellSlots]

    @property
    def embed_format(self) -> str:
        res = f"Sorcery Points: `{self.sorcery_points}`\n" \
              f"Metamagic Known: `{self.metamagic_known}`"
        if self.creating_spell_slots:
            res += "\nCreating Spell Slots:"
            for slot in self.creating_spell_slots:
                res += f"\n> {slot.embed_format}"

        return res


@dataclass
class ClassSpecificWarlock(APIModel):
    invocations_known: int
    mystic_arcanum_level_6: int
    mystic_arcanum_level_7: int
    mystic_arcanum_level_8: int
    mystic_arcanum_level_9: int

    @property
    def embed_format(self) -> str:
        return f"Invocations Known: `{self.invocations_known}`\n" \
               f"Mystic Arcanum Spells:\n" \
               f"> Level 6: `{self.mystic_arcanum_level_6}`\n" \
               f"> Level 7: `{self.mystic_arcanum_level_7}`\n" \
               f"> Level 8: `{self.mystic_arcanum_level_8}`\n" \
               f"> Level 9: `{self.mystic_arcanum_level_9}`"


@dataclass
class ClassSpecificWizard(APIModel):
    arcane_recovery_levels: int

    @property
    def embed_format(self) -> str:
        return f"Arcane Recovery Levels: `{self.arcane_recovery_levels}`"


@dataclass
class ClassLevel(ResourceModel):
    index: str
    url: str
    level: int
    ability_score_bonuses: int
    prof_bonus: int
    features: list[APIReference]
    class_: APIReference
    spellcasting: Optional[ClassLevelSpellcasting] = field(default=None)
    class_specific: Optional[Union[
        ClassSpecificCleric, ClassSpecificBarbarian, ClassSpecificBard,
        ClassSpecificDruid, ClassSpecificFighter, ClassSpecificMonk,
        ClassSpecificPaladin, ClassSpecificRanger, ClassSpecificRogue,
        ClassSpecificSorcerer, ClassSpecificWarlock, ClassSpecificWizard,
    ]] = field(default=None)


# ---------- Schemas ----------
class ClassLevelSpellcastingSchema(Schema):
    cantrips_known = fields.Int()
    spells_known = fields.Int()
    spell_slots_level_1 = fields.Int(required=True)
    spell_slots_level_2 = fields.Int(required=True)
    spell_slots_level_3 = fields.Int(required=True)
    spell_slots_level_4 = fields.Int(required=True)
    spell_slots_level_5 = fields.Int(required=True)
    spell_slots_level_6 = fields.Int()
    spell_slots_level_7 = fields.Int()
    spell_slots_level_8 = fields.Int()
    spell_slots_level_9 = fields.Int()

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassLevelSpellcasting(**data)


class ClassSpecificBarbarianSchema(Schema):
    rage_count = fields.Int(required=True)
    rage_damage_bonus = fields.Int(required=True)
    brutal_critical_dice = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificBarbarian(**data)


class ClassSpecificBardSchema(Schema):
    bardic_inspiration_die = fields.Int(required=True)
    song_of_rest_die = fields.Int(required=True)
    magical_secrets_max_5 = fields.Int(required=True)
    magical_secrets_max_7 = fields.Int(required=True)
    magical_secrets_max_9 = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificBard(**data)


class ClassSpecificClericSchema(Schema):
    channel_divinity_charges = fields.Int(required=True)
    destroy_undead_cr = fields.Float(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificCleric(**data)


class ClassSpecificDruidSchema(Schema):
    wild_shape_max_cr = fields.Float(required=True)
    wild_shape_swim = fields.Bool(required=True)
    wild_shape_fly = fields.Bool(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificDruid(**data)


class ClassSpecificFighterSchema(Schema):
    action_surges = fields.Int(required=True)
    indomitable_uses = fields.Int(required=True)
    extra_attacks = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificFighter(**data)


class ClassSpecificMonkMartialArtsSchema(Schema):
    dice_count = fields.Int(required=True)
    dice_value = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificMonkMartialArts(**data)


class ClassSpecificMonkSchema(Schema):
    ki_points = fields.Int(required=True)
    unarmored_movement = fields.Int(required=True)
    martial_arts = fields.Nested(ClassSpecificMonkMartialArtsSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificMonk(**data)


class ClassSpecificPaladinSchema(Schema):
    aura_range = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificPaladin(**data)


class ClassSpecificRangerSchema(Schema):
    favored_enemies = fields.Int(required=True)
    favored_terrain = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificRanger(**data)


class ClassSpecificRogueSneakAttackSchema(Schema):
    dice_count = fields.Int(required=True)
    dice_value = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificRogueSneakAttack(**data)


class ClassSpecificRogueSchema(Schema):
    sneak_attack = fields.Nested(ClassSpecificRogueSneakAttackSchema(), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificRogue(**data)


class ClassSpecificSorcererCreatingSpellSlotsSchema(Schema):
    spell_slot_level = fields.Int(required=True)
    sorcery_point_cost = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificSorcererCreatingSpellSlots(**data)


class ClassSpecificSorcererSchema(Schema):
    sorcery_points = fields.Int(required=True)
    metamagic_known = fields.Int(required=True)
    creating_spell_slots = fields.List(fields.Nested(ClassSpecificSorcererCreatingSpellSlotsSchema()), required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificSorcerer(**data)


class ClassSpecificWarlockSchema(Schema):
    invocations_known = fields.Int(required=True)
    mystic_arcanum_level_6 = fields.Int(required=True)
    mystic_arcanum_level_7 = fields.Int(required=True)
    mystic_arcanum_level_8 = fields.Int(required=True)
    mystic_arcanum_level_9 = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificWarlock(**data)


class ClassSpecificWizardSchema(Schema):
    arcane_recovery_levels = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassSpecificWizard(**data)


class ClassLevelSchema(Schema):
    index = fields.Str(required=True)
    url = fields.Str(required=True)
    level = fields.Int(required=True)
    ability_score_bonuses = fields.Int(required=True)
    prof_bonus = fields.Int(required=True)
    features = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    spellcasting = fields.Nested(ClassLevelSpellcastingSchema())
    class_specific = UnionField(fields=[
        fields.Nested(ClassSpecificClericSchema()),
        fields.Nested(ClassSpecificBarbarianSchema()),
        fields.Nested(ClassSpecificBardSchema()),
        fields.Nested(ClassSpecificDruidSchema()),
        fields.Nested(ClassSpecificFighterSchema()),
        fields.Nested(ClassSpecificMonkSchema()),
        fields.Nested(ClassSpecificPaladinSchema()),
        fields.Nested(ClassSpecificRangerSchema()),
        fields.Nested(ClassSpecificRogueSchema()),
        fields.Nested(ClassSpecificSorcererSchema()),
        fields.Nested(ClassSpecificWarlockSchema()),
        fields.Nested(ClassSpecificWizardSchema()),
    ])
    class_ = fields.Nested(APIReferenceSchema(), required=True, data_key="class")

    @post_load
    def make_api_model(self, data, **kwargs):
        return ClassLevel(**data)
