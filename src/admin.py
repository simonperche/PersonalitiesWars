import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.commands import slash_command, permissions, Option

from database import DatabaseDeck
import utils

class Admin(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @slash_command(description='Set the claiming interval in minutes for all users.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def set_claiming_interval(self, ctx, interval: int):
        DatabaseDeck.get().set_claiming_interval(ctx.guild.id, interval)
        await ctx.respond(f'Set to {interval}.')

    @slash_command(description='Set the number of rolls per hour for all users.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def set_nb_rolls_per_hour(self, ctx, nb_rolls: int):
        DatabaseDeck.get().set_nb_rolls_per_hour(ctx.guild.id, nb_rolls)
        await ctx.respond(f'Set to {nb_rolls}.')

    @slash_command(description='Set the amount of time to claim (in seconds) for all users.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def set_time_to_claim(self, ctx, time_to_claim: int):
        DatabaseDeck.get().set_time_to_claim(ctx.guild.id, time_to_claim)
        await ctx.respond(f'Set to {time_to_claim}')

    @slash_command(description='Set number of wishes allowed to a user.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def set_max_wish(self, ctx, user: Option(discord.Member), max_wish: int):
        DatabaseDeck.get().set_max_wish(ctx.guild.id, user.id, max_wish)
        await ctx.respond(f'Set {user.name if user.nick is None else user.name} number of wishes to {max_wish}.')

    @slash_command(aliases=['show_config'], description='Show the current configuration of the bot for this server.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def show_configuration(self, ctx):
        config = DatabaseDeck.get().get_server_configuration(ctx.guild.id)

        description = f'Claim interval: {config["claim_interval"]} minutes\n' \
                      f'Time to claim a personality: {config["time_to_claim"]} seconds\n' \
                      f'Number of rolls per hour: {config["rolls_per_hour"]}'

        embed = discord.Embed(title=f'Server *{ctx.guild.name}* configuration', description=description)
        await ctx.respond(embed=embed)

    @slash_command(description='Set the information channel where the bot can send message updates.',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def set_information_channel(self, ctx, channel: Option(discord.TextChannel, required=False, default=None)):
        if not channel:
            DatabaseDeck.get().set_information_channel(ctx.guild.id, None)
            await ctx.respond('I have removed information channel. You will not receive update anymore.')
            return

        DatabaseDeck.get().set_information_channel(ctx.guild.id, channel.id)
        await ctx.respond(f'Set to {channel.mention}.')

    @slash_command(description='Set the claims channel where users roll and '
                               'claim personalities (used to display a recap of claims)',
                   guild_ids=utils.get_authorized_guild_ids())
    @permissions.has_role("PersonalitiesWarsAdmin")
    async def set_claims_channel(self, ctx, channel: Option(discord.TextChannel, required=False, default=None)):
        if not channel:
            DatabaseDeck.get().set_claims_channel(ctx.guild.id, None)
            await ctx.respond('I have removed claims channel. You will not receive a recap anymore.')
            return

        DatabaseDeck.get().set_claims_channel(ctx.guild.id, channel.id)
        await ctx.respond(f'Set to {channel.mention}.')
