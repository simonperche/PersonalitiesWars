import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from database import DatabasePersonality, DatabaseDeck
import utils


class Wishlist(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @slash_command(description='Add a personality to your wish list.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def wish(self, ctx,
                   name: Option(str, 'Pick a name or write yours', autocomplete=utils.personalities_name_searcher),
                   group: Option(str, 'Pick a group or write yours', autocomplete=utils.personalities_group_searcher,
                                 required=False, default=None)):
        name = name.strip()

        if group:
            group = group.strip()

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.respond(f'Personality **{name}**{" from *" + group + "* " if group else ""} not found.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        nb_wish = DatabaseDeck.get().get_nb_wish(ctx.guild.id, ctx.author.id)
        max_wish = DatabaseDeck.get().get_max_wish(ctx.guild.id, ctx.author.id)

        if nb_wish >= max_wish:
            # Red cross
            await ctx.respond('Your wish list is full!')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        if DatabaseDeck.get().add_to_wishlist(ctx.guild.id, id_perso, ctx.author.id):
            # Green mark
            await ctx.respond(f'I added {name}.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.respond(f'You already have {name} in your wish list.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

    @slash_command(description='Remove a personality from your wish list',
                   guild_ids=utils.get_authorized_guild_ids())
    async def wishremove(self, ctx, name: Option(str, 'Pick a name or write yours',
                                                 autocomplete=utils.wishlist_name_searcher),
                         group: Option(str, 'Pick a group or write yours',
                                       autocomplete=utils.personalities_group_searcher, required=False, default=None)):
        name = name.strip()

        if group:
            group = group.strip()

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.respond(f'Personality **{name}**{" from *" + group + "* " if group else ""} not found.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        if DatabaseDeck.get().remove_from_wishlist(ctx.guild.id, id_perso, ctx.author.id):
            # Green mark
            await ctx.respond(f'I removed {name}.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.respond(f'You don\'t have {name} in your wish list.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

    @slash_command(description='Show your wishlist.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def wishlist(self, ctx, member: Option(discord.Member, required=False, default=None)):
        wishlist_owner = member or ctx.author

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

        await ctx.respond(embed=discord.Embed(title=f'Wish list of {username} ({nb_wish}/{max_wish})',
                                              description=description))
