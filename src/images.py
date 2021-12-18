import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from database import DatabasePersonality, DatabaseDeck
import utils

class Images(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @slash_command(description='Add a custom image to a personality.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def add_image(self, ctx, name: Option(str, "Pick a name or write yours", autocomplete=utils.personalities_name_searcher),
                        url: str):
        name = name.strip()

        id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.respond(f'Personality **{name}** not found.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        DatabasePersonality.get().add_image(id_perso, url)
        # Green mark
        await ctx.respond('Done.')
        msg = await ctx.interaction.original_message()
        await msg.add_reaction(u"\u2705")

    @slash_command(description='Remove an image of a personality."',
                   guild_ids=utils.get_authorized_guild_ids())
    async def remove_image(self, ctx, name: Option(str, "Pick a name or write yours", autocomplete=utils.personalities_name_searcher),
                           url: str):
        name = name.strip()

        id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.respond(f'Personality **{name}** not found.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        DatabasePersonality.get().remove_image(id_perso, url)
        # Green mark
        await ctx.respond('Done.')
        msg = await ctx.interaction.original_message()
        await msg.add_reaction(u"\u2705")
