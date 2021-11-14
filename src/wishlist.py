import discord
from discord.ext import commands

from database import DatabaseIdol, DatabaseDeck


class Wishlist(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(description='Add an idol to your wish list.'
                                  'Please add "" if it has spaces\n'
                                  'Take the first corresponding idol.'
                                  'See list command for all idols.\n'
                                  'Example:\n'
                                  '   *wish rm'
                                  '   *wish heejin loona'
                                  '   *wish joy "red velvet"')
    async def wish(self, ctx, name, group=None):
        name = name.strip()

        if group:
            group = group.strip()

        id_idol = None

        if group:
            id_idol = DatabaseIdol.get().get_idol_group_id(name, group)
        else:
            ids = DatabaseIdol.get().get_idol_ids(name)
            if ids:
                id_idol = ids[0]

        if not id_idol:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Idol **{name}**{" from *" + group + "* " if group else ""} not found.')
            return

        nb_wish = DatabaseDeck.get().get_nb_wish(ctx.guild.id, ctx.author.id)
        max_wish = DatabaseDeck.get().get_max_wish(ctx.guild.id, ctx.author.id)

        if nb_wish >= max_wish:
            # Red cross
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Your wish list is full!')
            return

        if DatabaseDeck.get().add_to_wishlist(ctx.guild.id, id_idol, ctx.author.id):
            # Green mark
            await ctx.message.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('You already have this idol in your wish list.')

    @commands.command(description='Remove an idol from your wish list. Please add "" if it has spaces\n'
                                  'Take the first corresponding idol. See list command for all idols.\n'
                                  'Example:\n'
                                  '   *wishremove rm'
                                  '   *wishremove heejin loona'
                                  '   *wishremove joy "red velvet"')
    async def wishremove(self, ctx, name, group=None):
        name = name.strip()

        if group:
            group = group.strip()

        id_idol = None

        if group:
            id_idol = DatabaseIdol.get().get_idol_group_id(name, group)
        else:
            ids = DatabaseIdol.get().get_idol_ids(name)
            if ids:
                id_idol = ids[0]

        if not id_idol:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'Idol **{name}**{" from *" + group + "* " if group else ""} not found.')
            return

        if DatabaseDeck.get().remove_from_wishlist(ctx.guild.id, id_idol, ctx.author.id):
            # Green mark
            await ctx.message.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('You don\'t have this idol in your wish list.')

    @commands.command(aliases=['wl'], description='Show your wishlist.')
    async def wishlist(self, ctx):
        ids = DatabaseDeck.get().get_wishlist(ctx.guild.id, ctx.author.id)

        description = ''
        username = ctx.author.name if ctx.author.nick is None else ctx.author.nick

        nb_wish = DatabaseDeck.get().get_nb_wish(ctx.guild.id, ctx.author.id)
        max_wish = DatabaseDeck.get().get_max_wish(ctx.guild.id, ctx.author.id)

        for id_idol in ids:
            current_image = DatabaseDeck.get().get_idol_current_image(ctx.guild.id, id_idol)
            idol = DatabaseIdol.get().get_idol_information(id_idol, current_image)
            id_owner = DatabaseDeck.get().idol_belongs_to(ctx.guild.id, id_idol)
            emoji = ''

            if id_owner:
                if id_owner == ctx.author.id:
                    emoji = u"\u2705"
                else:
                    emoji = u"\u274C"
            description += f'**{idol["name"]}** *{idol["group"]}* {emoji}\n'

        await ctx.send(embed=discord.Embed(title=f'Wish list of {username} ({nb_wish}/{max_wish})',
                                           description=description))
