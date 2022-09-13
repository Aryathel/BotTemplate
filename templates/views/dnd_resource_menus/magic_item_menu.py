from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.equipment import MagicItem


class MagicItemMenuPage(ResourceMenuPage):
    resource: 'MagicItem'

    async def generate_pages(self, interaction: Interaction) -> None:
        fields = [
            ('Equipment Category', f'`{self.resource.equipment_category.name}`'),
            ('Rarity', f'`{self.resource.rarity.name.value}`'),
            ('Is Variant', f'`{self.resource.variant}`'),
        ]
        if self.resource.variants:
            fields.append(('Variants', '\n'.join(f'`{v.name}`' for v in self.resource.variants), False))

        if len('\n\n'.join(self.resource.desc)) <= 4096:
            self.pages.append(self.embed_factory.get(
                description='\n\n'.join(self.resource.desc),
                fields=fields
            ))
        else:
            segments = self._truncated(self.resource.desc)

            for s in segments:
                self.pages.append(self.embed_factory.get(
                    description=s,
                    fields=fields
                ))

    @classmethod
    def _truncated(cls, desc: list[str]) -> list[str]:
        current = desc
        leftover = []
        exc = 0

        while len('\n\n'.join(current)) > 4096:
            exc += 1
            current = desc[:-exc]
            leftover = desc[-exc:]

        segments = ['\n\n'.join(current)]
        if leftover:
            segments += cls._truncated(leftover)
        return segments


class MagicItemMenu(ResourceMenu, page_type=MagicItemMenuPage):
    pass
