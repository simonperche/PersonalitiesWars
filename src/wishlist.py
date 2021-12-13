import discord
from discord.ext import commands

from database import DatabasePersonality, DatabaseDeck


class Wishlist(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(description='Add a personality to your wish list.'
                                  'Please add "" if it has spaces\n'
                                  'Take the first corresponding personality.'
                                  'See list command for all personalities.\n'
                                  'Example:\n'
                                  '   *wish "yoko taro"'
                                  '   *wish "Yannis Philippakis" SINGER')
    async def wish(self, ctx, name, group=None):
        name = name.strip()

        if group:
            group = group.strip()

        id_perso = None

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Personality **{name}**{" from *" + group + "* " if group else ""} not found.')
            return

        nb_wish = DatabaseDeck.get().get_nb_wish(ctx.guild.id, ctx.author.id)
        max_wish = DatabaseDeck.get().get_max_wish(ctx.guild.id, ctx.author.id)

        if nb_wish >= max_wish:
            # Red cross
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Your wish list is full!')
            return

        if DatabaseDeck.get().add_to_wishlist(ctx.guild.id, id_perso, ctx.author.id):
            # Green mark
            await ctx.message.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('You already have this personality in your wish list.')

    @commands.command(description='Remove a personality from your wish list. Please add "" if it has spaces\n'
                                  'Take the first corresponding personality. See list command for all personalities.\n'
                                  'Example:\n'
                                  '   *wishremove "yoko taro"'
                                  '   *wishremove "Yannis Philippakis" SINGER')
    async def wishremove(self, ctx, name, group=None):
        name = name.strip()

        if group:
            group = group.strip()

        id_perso = None

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Personality **{name}**{" from *" + group + "* " if group else ""} not found.')
            return

        if DatabaseDeck.get().remove_from_wishlist(ctx.guild.id, id_perso, ctx.author.id):
            # Green mark
            await ctx.message.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('You don\'t have this personality in your wish list.')

    @commands.command(aliases=['wl'], description='Show your wishlist.')
    async def wishlist(self, ctx):
        wishlist_owner = ctx.author if not ctx.message.mentions else ctx.message.mentions[0]

        ids = DatabaseDeck.get().get_wishlist(ctx.guild.id, wishlist_owner.id)

        description = ''
        username = wishlist_owner.name if wishlist_owner.nick is None else wishlist_owner.nick

        nb_wish = DatabaseDeck.get().get_nb_wish(ctx.guild.id, wishlist_owner.id)
        max_wish = DatabaseDeck.get().get_max_wish(ctx.guild.id, wishlist_owner.id)

        personalities = DatabasePersonality.get().get_multiple_perso_information(ids)
        if personalities:
            for i, perso in enumerate(personalities):
                id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, ids[i])
                emoji = ''

                if id_owner:
                    if id_owner == wishlist_owner.id:
                        emoji = u"\u2705"
                    else:
                        emoji = u"\u274C"
                description += f'**{perso["name"]}** *{perso["group"]}* {emoji}\n'

        await ctx.send(embed=discord.Embed(title=f'Wish list of {username} ({nb_wish}/{max_wish})',
                                           description=description))
