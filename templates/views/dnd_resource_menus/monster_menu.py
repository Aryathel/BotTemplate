from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage, select_option, ResourceMenuPageSelect

if TYPE_CHECKING:
    from apis.dnd5e.models.monsters import Monster


@select_option(
    label="General",
    description="General {name} monster information.",
    value="monster_general",
)
@select_option(
    label="Stats",
    description="{name} base stats.",
    value="monster_stats",
)
@select_option(
    label='Proficiencies',
    description="{name} proficiencies, resistances, and immunities.",
    value='monster_proficiencies'
)
@select_option(
    label='Actions',
    description="{name} actions.",
    value="monster_actions"
)
@select_option(
    label="Legendary Actions",
    description="{name} legendary actions.",
    value="monster_legendary_actions"
)
@select_option(
    label="Reactions",
    description="{name} reactions.",
    value="monster_reactions"
)
@select_option(
    label="Special Abilities",
    description="{name} special abilities.",
    value="monster_special_abilities"
)
class MonsterMenuPageSelect(ResourceMenuPageSelect):
    pass


class MonsterMenuPage(ResourceMenuPage):
    resource: 'Monster'
    included: dict[str, int]

    async def generate_pages(self, interaction: Interaction) -> None:
        self.included = {'General': len(self.pages) + 1}
        fields = [
            ('Type', f'`{self.resource.type.title()}`'),

        ]
        if self.resource.subtype:
            fields.append(('Subtype', f'`{self.resource.subtype.title()}`'))
        fields += [
            ('Size', f'`{self.resource.size.value}`'),
            ('Alignment', f'`{self.resource.alignment.value}`'),
            ('Challenge Rating', f'`{self.resource.challenge_rating}`'),
            ('XP', f'`{self.resource.xp}`'),
        ]
        if self.resource.languages:
            fields.append(('Languages', f'`{self.resource.languages}`'))
        if self.resource.forms:
            fields.append(('Other Forms', '\n'.join(f'`{f.name}`' for f in self.resource.forms), False))
        self.pages.append(self.embed_factory.get(
            author_name='General',
            description=self.resource.desc,
            fields=fields
        ))

        self.included['Stats'] = len(self.pages) + 1
        fields = [
            ('Hit Points', f"`{self.resource.hit_points}`"),
            ('Armor Class', f"`{self.resource.armor_class}`"),
            ('Speed', f'{self.resource.speed.embed_format}'),
            ('Hit Dice', f"`{self.resource.hit_dice}`"),
            (
                'Ability Scores',
                '\n'.join([
                    f'`STR: {self.resource.strength}`',
                    f'`DEX: {self.resource.dexterity}`',
                    f'`CON: {self.resource.constitution}`',
                    f'`INT: {self.resource.intelligence}`',
                    f'`WIS: {self.resource.wisdom}`',
                    f'`CHA: {self.resource.charisma}`',
                ]),
                False
            ),
        ]
        if self.resource.senses:
            fields.append(('Senses', self.resource.senses.embed_format, False))
        self.pages.append(self.embed_factory.get(
            author_name='Stats',
            fields=fields
        ))

        fields = []
        if self.resource.proficiencies:
            fields.append(('Proficiencies', '\n'.join(f'`{p.embed_format}`' for p in self.resource.proficiencies)))
        if self.resource.damage_vulnerabilities:
            fields.append(('Damage Vulnerabilities', '\n'.join(f'`{v}`' for v in self.resource.damage_vulnerabilities)))
        if self.resource.damage_resistances:
            fields.append(('Damage Resistances', '\n'.join(f'`{v}`' for v in self.resource.damage_resistances)))
        if self.resource.damage_immunities:
            fields.append(('Damage Immunities', '\n'.join(f'`{v}`' for v in self.resource.damage_immunities)))
        if self.resource.condition_immunities:
            fields.append(('Condition Immunities', '\n'.join(f'`{c.name}`' for c in self.resource.condition_immunities)))
        if fields:
            self.included['Proficiencies'] = len(self.pages) + 1
            self.pages.append(self.embed_factory.get(
                author_name='Proficiencies',
                fields=fields
            ))

        if self.resource.actions:
            self.included['Actions'] = len(self.pages) + 1
            for action in self.resource.actions:
                fields = []
                if action.multiattack_type:
                    if action.multiattack_type == 'actions' and action.actions:
                        fields.append(('Actions Taken', '\n'.join(f'`{a.embed_format}`' for a in action.actions)))
                    elif action.multiattack_type == 'action_options' and action.action_options:
                        fields.append((
                            f'Action Options: Choose {action.action_options.choose}',
                            action.action_options.embed_format
                        ))
                    else:
                        raise ValueError(
                            f"Multiattack Type {action.multiattack_type} not implemented for resource "
                            f"{self.resource.name}: {action.name}."
                        )
                if action.attack_bonus:
                    fields.append(('Attack Bonus', f'`{action.attack_bonus}`'))
                if action.dc:
                    fields.append(('DC', f'`{action.dc.embed_format}`'))
                if action.damage:
                    formatted = []
                    for d in action.damage:
                        form = d.embed_format
                        if form.startswith('`'):
                            formatted.append(form)
                        else:
                            formatted.append(f'`{form}`')
                    fields.append(('Damage', '\n'.join(formatted)))
                if action.usage:
                    fields.append(('Usage', f'`{action.usage.embed_format}`'))
                if action.attacks:
                    fields.append(('Attacks', '\n'.join(f'`{a.embed_format}`' for a in action.attacks)))
                if action.options:
                    fields.append((f'Options: Choose {action.options.choose}', action.options.embed_format))
                self.pages.append(self.embed_factory.get(
                    author_name=f'Actions: {action.name}',
                    description=f"__**{action.name}**__:\n{action.desc}",
                    fields=fields
                ))

        if self.resource.legendary_actions:
            self.included['Legendary Actions'] = len(self.pages) + 1
            for action in self.resource.legendary_actions:
                fields = []
                if action.multiattack_type:
                    if action.multiattack_type == 'actions' and action.actions:
                        fields.append(('Actions Taken', '\n'.join(f'`{a.embed_format}`' for a in action.actions)))
                    elif action.multiattack_type == 'action_options' and action.action_options:
                        fields.append((
                            f'Action Options: Choose {action.action_options.choose}',
                            action.action_options.embed_format
                        ))
                    else:
                        raise ValueError(
                            f"Multiattack Type {action.multiattack_type} not implemented for resource "
                            f"{self.resource.name}: {action.name}."
                        )
                if action.attack_bonus:
                    fields.append(('Attack Bonus', f'`{action.attack_bonus}`'))
                if action.dc:
                    fields.append(('DC', f'`{action.dc.embed_format}`'))
                if action.damage:
                    formatted = []
                    for d in action.damage:
                        form = d.embed_format
                        if form.startswith('`'):
                            formatted.append(form)
                        else:
                            formatted.append(f'`{form}`')
                    fields.append(('Damage', '\n'.join(formatted)))
                if action.usage:
                    fields.append(('Usage', f'`{action.usage.embed_format}`'))
                if action.attacks:
                    fields.append(('Attacks', '\n'.join(f'`{a.embed_format}`' for a in action.attacks)))
                if action.options:
                    fields.append((f'Options: Choose {action.options.choose}', action.options.embed_format))
                self.pages.append(self.embed_factory.get(
                    author_name=f'Legendary Actions: {action.name}',
                    description=f"__**{action.name}**__:\n{action.desc}",
                    fields=fields
                ))

        if self.resource.reactions:
            self.included['Reactions'] = len(self.pages) + 1
            for action in self.resource.reactions:
                fields = []
                if action.multiattack_type:
                    if action.multiattack_type == 'actions' and action.actions:
                        fields.append(('Actions Taken', '\n'.join(f'`{a.embed_format}`' for a in action.actions)))
                    elif action.multiattack_type == 'action_options' and action.action_options:
                        fields.append((
                            f'Action Options: Choose {action.action_options.choose}',
                            action.action_options.embed_format
                        ))
                    else:
                        raise ValueError(
                            f"Multiattack Type {action.multiattack_type} not implemented for resource "
                            f"{self.resource.name}: {action.name}."
                        )
                if action.attack_bonus:
                    fields.append(('Attack Bonus', f'`{action.attack_bonus}`'))
                if action.dc:
                    fields.append(('DC', f'`{action.dc.embed_format}`'))
                if action.damage:
                    formatted = []
                    for d in action.damage:
                        form = d.embed_format
                        if form.startswith('`'):
                            formatted.append(form)
                        else:
                            formatted.append(f'`{form}`')
                    fields.append(('Damage', '\n'.join(formatted)))
                if action.usage:
                    fields.append(('Usage', f'`{action.usage.embed_format}`'))
                if action.attacks:
                    fields.append(('Attacks', '\n'.join(f'`{a.embed_format}`' for a in action.attacks)))
                if action.options:
                    fields.append((f'Options: Choose {action.options.choose}', action.options.embed_format))
                self.pages.append(self.embed_factory.get(
                    author_name=f'Reactions: {action.name}',
                    description=f"__**{action.name}**__:\n{action.desc}",
                    fields=fields
                ))

        if self.resource.special_abilities:
            self.included['Special Abilities'] = len(self.pages) + 1
            for ability in self.resource.special_abilities:
                fields = []
                if ability.attack_bonus:
                    fields.append(('Attack Bonus', f'`{ability.attack_bonus}`'))
                if ability.damage:
                    fields.append(('Damage', '\n'.join(f'`{d.embed_format}`' for d in ability.damage)))
                if ability.dc:
                    fields.append(('DC', f'`{ability.dc.embed_format}`'))
                if ability.usage:
                    fields.append(('Usage', f'`{ability.usage.embed_format}`'))
                if ability.spellcasting:
                    if ability.spellcasting.level:
                        fields.append(('Spellcasting Level', f'`{ability.spellcasting.level}`'))
                    fields.append(('Spellcasting Ability', f'`{ability.spellcasting.ability.name}`'))
                    if ability.spellcasting.dc:
                        fields.append(('Spellcasting DC', f'`{ability.spellcasting.dc}`'))
                    if ability.spellcasting.modifier:
                        fields.append(('Spellcasting Modifier', f'`{ability.spellcasting.modifier}`'))
                    if ability.spellcasting.school:
                        fields.append(('Spellcasting School', f'`{ability.spellcasting.school}`'))
                    if ability.spellcasting.components_required:
                        fields.append((
                            'Components Required',
                            ', '.join(f'`{a}`' for a in ability.spellcasting.components_required)
                        ))
                    if ability.spellcasting.slots:
                        fields.append((
                            'Spellcasting Slots',
                            '\n'.join(f'`Level {k}: {v}`' for k, v in ability.spellcasting.slots.items()),
                            False
                        ))
                    if ability.spellcasting.spells:
                        spells = {}
                        for spell in ability.spellcasting.spells:
                            if spell.level not in spells:
                                spells[spell.level] = []
                            spells[spell.level].append(f'`{spell.name}`')
                        for k, v in spells.items():
                            spells[k] = '\n'.join(v)
                        spells = sorted(spells.items())
                        fields.append((
                            'Spellcasting Spells',
                            '\n'.join(f'__Level {k}:__\n{v}' for k, v in spells),
                            False
                        ))
                self.pages.append(self.embed_factory.get(
                    author_name=f'Special Ability: {ability.name}',
                    description=f"__**{ability.name}**__:\n{ability.desc}",
                    fields=fields,
                ))


class MonsterMenu(ResourceMenu, page_type=MonsterMenuPage, select_type=MonsterMenuPageSelect):
    pass
