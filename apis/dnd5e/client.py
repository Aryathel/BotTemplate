from typing import Tuple, Mapping, Any, Union

import aiohttp_client_cache
from marshmallow import ValidationError
from marshmallow.base import SchemaABC
from async_property import async_cached_property

from templates.errors import SchemaError

from .models import ResourceModel
from .models.class_levels import ClassLevelSchema
from .models.common import APIReferenceListSchema, APIReferenceList
from .models.character_data import AbilityScoreSchema, AlignmentSchema, BackgroundSchema, LanguageSchema, \
    ProficiencySchema, SkillSchema
from .models.class_ import ClassSchema
from .models.game_mechanics import ConditionSchema, DamageTypeSchema, MagicSchoolSchema
from .models.equipment import WeaponSchema, ArmorSchema, GearSchema, EquipmentPackSchema, ToolSchema, VehicleSchema, \
    EquipmentCategorySchema, MagicItemSchema, WeaponPropertySchema
from .models.feats import FeatSchema
from .models.features import FeatureSchema
from .models.general import APIReference
from .models.monsters import MonsterSchema
from .models.races import RaceSchema
from .models.rules import RuleSectionSchema, RuleSchema
from .models.spells import SpellSchema
from .models.subclasses import SubclassSchema
from .models.subclass_levels import SubclassLevelSchema
from .models.subraces import SubraceSchema
from .models.traits import TraitSchema
from .utils import populated, with_resource_cache

BASE_URL = "https://www.dnd5eapi.co"


class DnD5e:
    lookup_schema_mapping = {
        # Character Data
        'ability-scores': AbilityScoreSchema(),
        'alignments': AlignmentSchema(),
        'backgrounds': BackgroundSchema(),
        'languages': LanguageSchema(),
        'proficiencies': ProficiencySchema(),
        'skills': SkillSchema(),

        # Class
        'classes': ClassSchema(),

        # Game Mechanics
        'conditions': ConditionSchema(),
        'damage-types': DamageTypeSchema(),
        'magic-schools': MagicSchoolSchema(),

        # Equipment
        'equipment': [
            WeaponSchema(),
            VehicleSchema(),
            EquipmentPackSchema(),
            ToolSchema(),
            GearSchema(),
            ArmorSchema(),
        ],
        'equipment-categories': EquipmentCategorySchema(),
        'magic-items': MagicItemSchema(),
        'weapon-properties': WeaponPropertySchema(),

        # Feats
        'feats': FeatSchema(),

        # Features
        'features': FeatureSchema(),

        # Monsters
        'monsters': MonsterSchema(),

        # Races
        'races': RaceSchema(),

        # Rules
        'rule-sections': RuleSectionSchema(),
        'rules': RuleSchema(),

        # Spells
        'spells': SpellSchema(),

        # Subclasses
        'subclasses': SubclassSchema(),

        # Subraces
        'subraces': SubraceSchema(),

        # Traits
        'traits': TraitSchema(),
    }
    api_ref_list_schema = APIReferenceListSchema()
    class_level_schema = ClassLevelSchema()
    subclass_level_schema = SubclassLevelSchema()

    session: aiohttp_client_cache.CachedSession
    _endpoints: Mapping[str, str]
    _resource_cache: Mapping[str, Mapping[str, dict[str, Tuple[APIReference, str]]]]

    def __init__(self):
        self.cache = aiohttp_client_cache.SQLiteBackend(cache_name="./cache/dnd_cache.sqlite", expire_after=86400)
        self.session = aiohttp_client_cache.CachedSession(base_url=BASE_URL, cache=self.cache)

    @async_cached_property
    async def endpoints(self) -> Mapping[str, str]:
        if not hasattr(self, '_endpoints'):
            self._endpoints = await self.get_all_resource_endpoints()

        return self._endpoints

    @async_cached_property
    async def resource_cache(self) -> Mapping[str, Mapping[str, dict[str, Tuple[APIReference, str]]]]:
        if not hasattr(self, '_resource_cache'):
            self._resource_cache = {}
            for endpoint in (await self.endpoints).keys():
                self._resource_cache[endpoint] = {}
                for ref in (await self.get_resources_for_endpoint(endpoint)).results:
                    self._resource_cache[endpoint][ref.index] = (ref, endpoint)

        return self._resource_cache

    async def get_all_resource_endpoints(self) -> Mapping[str, str]:
        async with self.session.get('/api') as r:
            r.raise_for_status()
            return await r.json()

    @populated
    async def get_resources_for_endpoint(self, endpoint: str) -> APIReferenceList:
        route = self.endpoints.get(endpoint)
        if not route:
            raise ValueError(f"No route for endpoint \"{endpoint}\"")

        async with self.session.get(route) as r:
            r.raise_for_status()
            return self.api_ref_list_schema.load(await r.json())

    @with_resource_cache
    async def lookup(self, index: Tuple[APIReference, str]) -> Tuple[ResourceModel, SchemaABC]:
        ref, endpoint = index
        schema = self.lookup_schema_mapping.get(endpoint)
        if not schema:
            raise SchemaError(endpoint=endpoint)

        async with self.session.get(ref.url) as r:
            r.raise_for_status()
            if isinstance(schema, list):
                dt = await r.json()
                e = []
                for sc in schema:
                    try:
                        return sc.load(dt), sc
                    except ValidationError as err:
                        e.append(err)
                        continue
                raise ValidationError(e)
            else:
                return schema.load(await r.json()), schema

    async def lookup_raw(self, route: str, response_model: SchemaABC, is_list: bool = False) -> Union[Any, list[Any]]:
        async with self.session.get(route) as r:
            r.raise_for_status()
            if is_list:
                response = []
                for entry in await r.json():
                    response.append(response_model.load(entry))
                return response
            return response_model.load(await r.json())
