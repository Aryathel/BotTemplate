from typing import TYPE_CHECKING

from ...bot import Interaction
from .framework import ResourceMenu, ResourceMenuPage

if TYPE_CHECKING:
    from apis.dnd5e.models.rules import RuleSection


class RuleSectionMenuPage(ResourceMenuPage):
    resource: 'RuleSection'

    async def generate_pages(self, interaction: Interaction) -> None:
        desc_split = self.resource.desc.split('\n\n')

        segments = [desc_split[0]]
        for section in desc_split[1:]:
            if len(segments[-1]) + len('\n\n') + len(section) > 4050:
                segments.append(section)
            else:
                segments[-1] += '\n\n' + section

        for segment in segments:
            self.pages.append(self.embed_factory.get(
                description=segment,
            ))


class RuleSectionMenu(ResourceMenu, page_type=RuleSectionMenuPage):
    pass
