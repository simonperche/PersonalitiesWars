import discord
from discord.ext import commands

from database import DatabaseIdol, DatabaseDeck


class Images(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(description='Add a custom image to an idol."')
    async def add_image(self, ctx, name, url):
        name = name.strip()

        id_idol = None

        ids = DatabaseIdol.get().get_idol_ids(name)
        if ids:
            id_idol = ids[0]

        if not id_idol:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Idol **{name}** not found.')
            return

        if not url:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Please give an URL to the image.')
            return

        DatabaseIdol.get().add_image(id_idol, url)
        # Green mark
        await ctx.message.add_reaction(u"\u2705")

    @commands.command(description='Remove an image of an idol."')
    async def remove_image(self, ctx, name, url):
        name = name.strip()

        id_idol = None

        ids = DatabaseIdol.get().get_idol_ids(name)
        if ids:
            id_idol = ids[0]

        if not id_idol:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Idol **{name}** not found.')
            return

        DatabaseIdol.get().remove_image(id_idol, url)
        # Green mark
        await ctx.message.add_reaction(u"\u2705")
