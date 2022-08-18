from typing import Union, cast, Tuple, Mapping

import aiohttp
import discord
from discord import app_commands
import yaml

from apis.dnd5e.models.general import APIReference
from templates import GroupCog, Interaction, Bot
from templates.errors import SchemaError
from templates.types import DiceRoll
from templates.views import DiceRollMenu, DiceRollPage
from templates import decorators, transformers, checks
from utils import EmbedFactory, Menu, MenuPageList
from utils.images import get_roll_text
from apis.dnd5e import DnD5e
from apis.dnd5e.models import APIReferenceList, ResourceModel


class DnDCog(GroupCog, group_name="dnd", name="dungeons&dragons"):
    description = "Commands related to Dungeons & Dragons."
    icon = "\N{DRAGON}"
    slash_commands = ['roll', 'lookup', 'apilookup', 'walkapi']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot.dnd_client = DnD5e()
        self.embeds: EmbedFactory = self.bot.embeds.copy()
        self.embeds.update(footer=f"Data from dnd5eapi.co")

    async def cog_load(self) -> None:
        self.bot.log('Loading DnD API client resource cache...')
        await self.bot.dnd_client.resource_cache
        self.bot.log('Loaded DnD API client resource cache.')

        await super().cog_load()

    @decorators.command(
        name="roll",
        description="Rolls dice using D&D standards.",
        icon="\N{GAME DIE}"
    )
    @app_commands.describe(
        rolls="The rolls that are thrown. More than one roll can be combined. Example: `2d20 kh1 +2`",
        private="Whether or not the roll will be visible to other people.",
        to="DMs the result of the role to the specified user, and then posts the results privately to the roller.",
    )
    async def dnd_roll_command(
            self,
            interaction: Interaction,
            rolls: app_commands.Transform[Union[DiceRoll, list[DiceRoll]], transformers.DiceRollTransformer],
            private: bool = False,
            to: discord.User = None,
    ) -> None:
        rolls: Union[DiceRoll, list[DiceRoll]] = cast(Union[DiceRoll, list[DiceRoll]], rolls)
        if isinstance(rolls, list):
            for r in rolls:
                r.roll()
        else:
            rolls.roll()
            rolls = [rolls]

        if to:
            private = True
            menu = DiceRollMenu(DiceRollPage(rolls, self.bot.embeds), interaction)
            await menu.send(to, f"{interaction.user.mention} Rolled")

        menu = DiceRollMenu(DiceRollPage(rolls, self.bot.embeds), interaction, private)
        await menu.start()

    @decorators.command(
        name='lookup',
        description="Look up standard information from the DnD 5e API.",
        help="Used for testing API endpoints during development.",
        icon="\N{PERSONAL COMPUTER}"
    )
    @app_commands.describe(
        endpoint="The type of data to look up. Leave blank to see available options.",
        lookup="The value to actually look up. Leave blank to see available options."
    )
    async def dnd_lookup_command(
            self,
            interaction: Interaction,
            endpoint: app_commands.Transform[str, transformers.DnDResourceTransformer],
            lookup: app_commands.Transform[Tuple[APIReference, str], transformers.DnDResourceLookupTransformer] = None,
    ) -> None:
        endpoint: str = cast(str, endpoint)
        lookup: Tuple[APIReference, str] = cast(Tuple[APIReference, str], lookup)

        if not lookup:
            resources = self.bot.dnd_client.resource_cache.get(endpoint).values()
            await Menu(MenuPageList(
                factory=self.embeds,
                items=[r[0].name for r in resources],
                title=endpoint.replace('-', ' ').title(),
                url=f"https://www.dnd5eapi.co/api/{endpoint}",
                number_items=True,
            ), interaction).start()

        else:
            res, _ = await self.bot.dnd_client.lookup(lookup)

            try:
                await res.to_menu(interaction, self.embeds).start()
            except NotImplementedError as e:
                raise e
                emb = self.bot.embeds.get(
                    description=f"Display not yet implemented for endpoint `{endpoint.replace('-', ' ').title()}`."
                )
                await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='lookupdev',
        description="Nothing to see here...nothing at all...",
        help="Used for testing API endpoints during development. Requires `administrator` permissions.",
        icon="\N{PERSONAL COMPUTER}"
    )
    @app_commands.describe(
        endpoint="The type of data to look up. Leave blank to see available options.",
        lookup="The value to actually look up. Leave blank to see available options."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def dnd_api_command(
            self,
            interaction: Interaction,
            endpoint: app_commands.Transform[str, transformers.DnDResourceTransformer] = None,
            lookup: app_commands.Transform[Tuple[APIReference, str], transformers.DnDResourceLookupTransformer] = None,
    ) -> None:
        endpoint: str = cast(str, endpoint)
        lookup: Tuple[APIReference, str] = cast(Tuple[APIReference, str], lookup)

        truncated = False

        # Handle getting the data
        if lookup:
            try:
                res, schema = await self.bot.dnd_client.lookup(lookup)
            except ValueError:
                emb = self.bot.embeds.get(description=f"No route found for endpoint `{endpoint}`.")
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return
            except SchemaError:
                emb = self.bot.embeds.get(description=f"No response schema found for endpoint `{endpoint}`.")
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return
            except aiohttp.ClientResponseError:
                emb = self.bot.embeds.get(description=f"Could not find index `{lookup}` for endpoint `{endpoint.replace('-', ' ').title()}`.")
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

            title = res.name
            self.bot.debug(res)
            res: dict = schema.dump(res)
        elif endpoint:
            try:
                res: APIReferenceList = await self.bot.dnd_client.get_resources_for_endpoint(endpoint)
                self.bot.debug(res)
                schema = self.bot.dnd_client.api_ref_list_schema
            except ValueError:
                emb = self.bot.embeds.get(description=f"No route found for endpoint `{endpoint}`.")
                await interaction.response.send_message(embed=emb, ephemeral=True)
                return

            if res.count > 50:
                res.results = res.results[:50]
                truncated = True
            title = f"All {endpoint.replace('-', ' ').title()} Resources"

            res = schema.dump(res)
        else:
            res: Mapping[str, str] = await self.bot.dnd_client.get_all_resource_endpoints()
            title = "All API Resource Endpoints"

        # Log the data
        self.bot.debug(res)
        res = yaml.dump(res)
        if len(res) > 4075:
            truncated = True
            res = res[:4075]

        # Format response as YAML
        emb = self.bot.embeds.get(
            title=title,
            description=f'```yml\n{res}\n```',
            footer="Truncated data to fit in embed" if truncated else None
        )

        # Protect against large embed content (response size is arbitrary)
        try:
            await interaction.response.send_message(embed=emb, ephemeral=True)
        except discord.HTTPException:
            emb = self.bot.embeds.get(description="Content too large for embed.")
            await interaction.response.send_message(embed=emb, ephemeral=True)

    @decorators.command(
        name='walkapi',
        description="This... could take a while.",
        help="This is restricted to the bot owner. This gets every endpoint, in order.",
    )
    @app_commands.rename(resource_endpoint="endpoint")
    @app_commands.describe(
        resource_endpoint='The endpoint to walk through the resources of. Used for limiting the test parameters.'
    )
    @checks.is_owner()
    async def dnd_api_walk_command(
            self,
            interaction: Interaction,
            resource_endpoint: app_commands.Transform[str, transformers.DnDResourceTransformer] = None,
    ) -> None:
        total = 0
        success = 0
        fail = 0
        schema_fail = 0

        success_icon = "\N{WHITE HEAVY CHECK MARK}"
        failure_icon = "\N{CROSS MARK}"

        self.bot.debug('Walking API', divider=True, urgent=True)
        await interaction.response.defer(thinking=True, ephemeral=True)

        start = discord.utils.utcnow()

        if not resource_endpoint:
            title = "All Resource Endpoints"
            endpoints = await self.bot.dnd_client.endpoints
            self.bot.ok(title, endpoints)

            for endpoint, route in endpoints.items():
                title = f"Walk All {endpoint} Resources"
                resources: list[tuple[APIReference, str]] = (await self.bot.dnd_client.resource_cache).get(endpoint).values()
                self.bot.dnd_client.api_ref_list_schema.dump(resources)
                self.bot.ok(title, resources)

                for ref in resources:
                    title = f"{total+1}: Get \"{ref[0].index}\" \"{endpoint}\" Resource"
                    try:
                        lookup, schema = await self.bot.dnd_client.lookup(ref)
                        schema.dump(lookup)
                        self.bot.ok(title, lookup, nest=1)
                        success += 1
                    except Exception as err:
                        if isinstance(err, SchemaError):
                            self.bot.error(f"{title} - SCHEMA NOT FOUND: {endpoint}", nest=1)
                            schema_fail += 1
                        else:
                            self.bot.error(title, error=err, nest=1)
                            return
                        fail += 1
                        continue
                    finally:
                        total += 1
        else:
            resources: Mapping[str, tuple[APIReference, str]] = self.bot.dnd_client.resource_cache.get(resource_endpoint)
            if not resources:
                emb = self.bot.embeds.get(description=f'No route found for endpoint {resource_endpoint}.')
                await interaction.followup.send(embed=emb, ephemeral=True)
                return

            title = f"Walk All {resource_endpoint} Resources"
            self.bot.ok(title, resources)

            resources: list[tuple[APIReference, str]] = list(resources.values())
            if resources:
                for index in resources:
                    title = f"{total+1}: Get \"{index[0].index}\" \"{resource_endpoint}\" Resource"
                    try:
                        lookup, schema = await self.bot.dnd_client.lookup(index)
                        schema.dump(lookup)
                        self.bot.ok(title, lookup, nest=1)
                        success += 1
                    except Exception as err:
                        if isinstance(err, SchemaError):
                            self.bot.error(f"{title} - SCHEMA NOT FOUND: {resource_endpoint}", nest=1)
                            schema_fail += 1
                        else:
                            self.bot.error(title, error=err, nest=1)
                        fail += 1
                        continue
                    finally:
                        total += 1

        runtime = discord.utils.utcnow() - start
        minutes, seconds = divmod(int(runtime.total_seconds()), 60)

        img = get_roll_text(f"{int(success/total*100)}%")
        img.seek(0)

        file = discord.File(img, filename='image.png')

        emb = self.bot.embeds.get(
            title=(
                f"{resource_endpoint.replace('-', ' ').title() if resource_endpoint else 'API'} "
                f"Walk Results: {failure_icon if fail else success_icon}"
            ),
            description=f"`Total`: `{total}`\n`Success`: `{success}`\n`Failed`: `{fail}`",
            thumbnail="attachment://image.png",
            footer=f"Run Time: {minutes} minute{'' if minutes == 1 else 's'}, {seconds} second{'' if seconds == 1 else 's'}"
        )
        if schema_fail:
            emb.description += f'\n`Missing Schema Fails`: `{schema_fail}`\n`Other Errors`: `{fail-schema_fail}`'
        await interaction.followup.send(embed=emb, file=file, ephemeral=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(DnDCog(bot), guilds=[bot.GUILD])
