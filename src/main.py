import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from roll import Roll
from admin import Admin
from profile import Profile
from information import Information
from wishlist import Wishlist
from trade import Trade
from images import Images
from badge import Badge
from shopping_list import ShoppingList
import utils

intents = discord.Intents.default()
intents.members = True

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = commands.Bot(command_prefix='*', intents=intents)

# TODO: If pages in paginator are empty, crash because of None send in embed instead of MISSING from discord.utils
bot.add_cog(Roll(bot))
bot.add_cog(Admin(bot))
bot.add_cog(Profile(bot))
bot.add_cog(Information(bot))
bot.add_cog(Wishlist(bot))
bot.add_cog(Trade(bot))
bot.add_cog(Images(bot))
bot.add_cog(Badge(bot))
bot.add_cog(ShoppingList(bot))


#### Bot commands ####

@bot.slash_command(guild_ids=utils.get_authorized_guild_ids())
async def ping(ctx):
    await ctx.respond('Yup, I\'m awake.', delete_after=5)


#### Bot event handlers ####

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for guild in utils.get_authorized_guild_ids():
        print(bot.get_guild(guild))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Unknown command.')
        return
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You're not authorized to execute this command.")
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments. *help for display help")
        return
    raise error


#### Utilities functions ####


#### Launch bot ####

bot.run(BOT_TOKEN)
