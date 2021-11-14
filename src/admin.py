import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

from database import DatabaseDeck

class Admin(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(description='Set the claiming interval in minutes for all users.')
    @has_permissions(administrator=True)
    async def set_claiming_interval(self, ctx, interval):
        try:
            interval = int(interval)
        except ValueError:
            await ctx.send('Please enter minutes as number.')
            await ctx.message.add_reaction(u"\u274C")
            return

        DatabaseDeck.get().set_claiming_interval(ctx.guild.id, interval)
        await ctx.message.add_reaction(u"\u2705")

    @commands.command(description='Set the number of rolls per hour for all users.')
    @has_permissions(administrator=True)
    async def set_nb_rolls_per_hour(self, ctx, nb_rolls):
        try:
            nb_rolls = int(nb_rolls)
        except ValueError:
            await ctx.send('Please enter number of rolls as number.')
            await ctx.message.add_reaction(u"\u274C")
            return

        DatabaseDeck.get().set_nb_rolls_per_hour(ctx.guild.id, nb_rolls)
        await ctx.message.add_reaction(u"\u2705")

    @commands.command(description='Set the amount of time to claim (in seconds) for all users.')
    @has_permissions(administrator=True)
    async def set_time_to_claim(self, ctx, time_to_claim):
        try:
            time_to_claim = int(time_to_claim)
        except ValueError:
            await ctx.send('Please enter time to claim as number.')
            await ctx.message.add_reaction(u"\u274C")
            return

        DatabaseDeck.get().set_time_to_claim(ctx.guild.id, time_to_claim)
        await ctx.message.add_reaction(u"\u2705")

    @commands.command(description='Set number of wishes allowed to a user. '
                                  'Please use discord mention to indicate the user.')
    @has_permissions(administrator=True)
    async def set_max_wish(self, ctx, max_wish):
        if not ctx.message.mentions:
            await ctx.send('Please mention a user.')
            await ctx.message.add_reaction(u"\u274C")
            return

        user = ctx.message.mentions[0]

        try:
            max_wish = int(max_wish)
        except ValueError:
            await ctx.send('Please enter a number.')
            await ctx.message.add_reaction(u"\u274C")
            return

        DatabaseDeck.get().set_max_wish(ctx.guild.id, user.id, max_wish)
        await ctx.message.add_reaction(u"\u2705")

    @commands.command(aliases=['show_config'], description='Show the current configuration of the bot for this server.')
    @has_permissions(administrator=True)
    async def show_configuration(self, ctx):
        config = DatabaseDeck.get().get_server_configuration(ctx.guild.id)

        description = f'Claim interval: {config["claim_interval"]} minutes\n' \
                      f'Time to claim a personality: {config["time_to_claim"]} seconds\n' \
                      f'Number of rolls per hour: {config["rolls_per_hour"]}'

        embed = discord.Embed(title=f'Server *{ctx.guild.name}* configuration', description=description)
        await ctx.send(embed=embed)
