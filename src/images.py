import discord
from discord.ext import commands

from database import DatabasePersonality, DatabaseDeck


class Images(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(description='Add a custom image to a personality."')
    async def add_image(self, ctx, name, url):
        name = name.strip()

        id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Personality **{name}** not found.')
            return

        if not url:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Please give an URL to the image.')
            return

        DatabasePersonality.get().add_image(id_perso, url)
        # Green mark
        await ctx.message.add_reaction(u"\u2705")

    @commands.command(description='Remove an image of a personality."')
    async def remove_image(self, ctx, name, url):
        name = name.strip()

        id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Personality **{name}** not found.')
            return

        DatabasePersonality.get().remove_image(id_perso, url)
        # Green mark
        await ctx.message.add_reaction(u"\u2705")
