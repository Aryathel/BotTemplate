from dataclasses import dataclass, field
from typing import Optional, Mapping, Union

from marshmallow import Schema, fields, post_load

from .framework import ResourceModel, APIModel, UnionField
from .general import APIReference, APIReferenceSchema


# ---------- Dataclasses ----------
@dataclass
class SubclassLevelSpellcasting(APIModel):
    cantrips_known: int
    spells_known: int
    spell_slots_level_1: int
    spell_slots_level_2: int
    spell_slots_level_3: int
    spell_slots_level_4: int
    spell_slots_level_5: int
    spell_slots_level_6: int
    spell_slots_level_7: int
    spell_slots_level_8: int
    spell_slots_level_9: int

    @property
    def embed_format(self) -> str:
        return f'Cantrips Known: `{self.cantrips_known}`\n' \
               f'Spells Known: `{self.spells_known}`\n' \
               f'Level 1 Spell Slots: `{self.spell_slots_level_1}`\n' \
               f'Level 2 Spell Slots: `{self.spell_slots_level_2}`\n' \
               f'Level 3 Spell Slots: `{self.spell_slots_level_3}`\n' \
               f'Level 4 Spell Slots: `{self.spell_slots_level_4}`\n' \
               f'Level 5 Spell Slots: `{self.spell_slots_level_5}`\n' \
               f'Level 6 Spell Slots: `{self.spell_slots_level_6}`\n' \
               f'Level 7 Spell Slots: `{self.spell_slots_level_7}`\n' \
               f'Level 8 Spell Slots: `{self.spell_slots_level_8}`\n' \
               f'Level 9 Spell Slots: `{self.spell_slots_level_9}`\n'


@dataclass
class SubclassLevelClassSpecific(APIModel):
    # Bard: Lore
    additional_magical_secrets_max_lvl: Optional[int] = field(default=None)

    # Paladin: Devotion
    aura_range: Optional[int] = field(default=None)

    @property
    def embed_format(self) -> str:
        res = []
        if self.additional_magical_secrets_max_lvl:
            res.append(f'Additional Magical Secrets Max Level: `{self.additional_magical_secrets_max_lvl}`')
        if self.aura_range:
            res.append(f'Aura Range: `{self.aura_range}`')
        return '\n'.join(res) if res else None


@dataclass
class SubclassLevel(ResourceModel):
    index: str
    url: str
    level: int
    features: list[APIReferenceSchema]
    class_: APIReference
    subclass: APIReference
    ability_score_bonuses: Optional[int] = field(default=None)
    prof_bonus: Optional[int] = field(default=None)
    spellcasting: Optional[SubclassLevelSpellcasting] = field(default=None)
    subclass_specific: Optional[SubclassLevelClassSpecific] = field(default=None)


# ---------- Schemas ----------
class SubclassLevelSpellcastingSchema(Schema):
    cantrips_known = fields.Int(required=True)
    spells_known = fields.Int(required=True)
    spell_slots_level_1 = fields.Int(required=True)
    spell_slots_level_2 = fields.Int(required=True)
    spell_slots_level_3 = fields.Int(required=True)
    spell_slots_level_4 = fields.Int(required=True)
    spell_slots_level_5 = fields.Int(required=True)
    spell_slots_level_6 = fields.Int(required=True)
    spell_slots_level_7 = fields.Int(required=True)
    spell_slots_level_8 = fields.Int(required=True)
    spell_slots_level_9 = fields.Int(required=True)

    @post_load
    def make_api_model(self, data, **kwargs):
        return SubclassLevelSpellcasting(**data)


class SubclassLevelClassSpecificSchema(Schema):
    additional_magical_secrets_max_lvl = fields.Int(required=False)
    aura_range = fields.Int(required=False)

    @post_load
    def make_api_model(self, data, **kwargs):
        return SubclassLevelClassSpecific(**data)


class SubclassLevelSchema(Schema):
    index = fields.Str(required=True)
    url = fields.Str(required=True)
    level = fields.Int(required=True)
    ability_score_bonuses = fields.Int(required=False)
    prof_bonus = fields.Int(required=False)
    class_ = fields.Nested(APIReferenceSchema(), required=True, data_key='class')
    subclass = fields.Nested(APIReferenceSchema(), required=True)
    features = fields.List(fields.Nested(APIReferenceSchema()), required=True)
    spellcasting = fields.Nested(SubclassLevelSpellcastingSchema(), required=False)
    subclass_specific = fields.Nested(SubclassLevelClassSpecificSchema(), required=False)

    @post_load
    def make_api_model(self, data, **kwargs):
        return SubclassLevel(**data)
