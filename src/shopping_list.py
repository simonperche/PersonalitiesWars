from collections import defaultdict

import discord
from discord.ext import commands, pages
from discord.commands import slash_command, Option

from database import DatabasePersonality, DatabaseDeck
import utils


class ShoppingList(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    @slash_command(description='Add a personality to your shopping list. Another member should own them.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def add_to_shopping_list(self, ctx,
                                   name: Option(str, 'Pick a name or write yours',
                                                autocomplete=utils.personalities_name_searcher),
                                   group: Option(str, 'Pick a group or write yours',
                                                 autocomplete=utils.personalities_group_searcher,
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

        id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)
        if not id_owner:
            await ctx.respond(f'Unfortunately, {name} does not belong to anyone. '
                              f'You can only add the personalities of other members.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        if DatabaseDeck.get().add_to_shopping_list(ctx.guild.id, id_perso, ctx.author.id):
            # Green mark
            await ctx.respond(f'{name} added.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.respond(f'You already have {name} in your shopping list.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

    @slash_command(description='Remove a personality from your shopping list.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def remove_from_shopping_list(self, ctx, name: Option(str, 'Pick a name or write yours',
                                                                autocomplete=utils.shopping_list_name_searcher),
                                        group: Option(str, 'Pick a group or write yours',
                                                      autocomplete=utils.personalities_group_searcher, required=False,
                                                      default=None)):
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

        if DatabaseDeck.get().remove_from_shopping_list(ctx.guild.id, id_perso, ctx.author.id):
            # Green mark
            await ctx.respond(f'{name} removed.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u2705")
        else:
            # Red cross
            await ctx.respond(f'You don\'t have {name} in your shopping list.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

    @slash_command(description='Show your shopping list.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def shopping_list(self, ctx, member: Option(discord.Member, required=False, default=None)):
        await ctx.defer()
        shopping_list_owner = member or ctx.author

        ids = DatabaseDeck.get().get_shopping_list(ctx.guild.id, shopping_list_owner.id)

        shopping_list_dict = defaultdict(list)
        username = shopping_list_owner.name if shopping_list_owner.nick is None else shopping_list_owner.nick

        personalities = DatabasePersonality.get().get_multiple_perso_information(ids)
        if personalities:
            for i, perso in enumerate(personalities):
                id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, ids[i])

                # Do not show if the personality belongs to nobody. May be the case with discard.
                if not id_owner:
                    continue

                shopping_list_dict[id_owner].append(f'**{perso["name"]}** *{perso["group"]}*')

        for user in shopping_list_dict.keys():
            shopping_list_dict[user].sort()

        nb_per_page = 20
        shopping_list_pages = []

        while True:
            if not shopping_list_dict:
                break

            embed = discord.Embed(title=f'Shopping list of {username}')

            total_persos = 0

            for user in sorted(shopping_list_dict.keys()):
                owner = ctx.guild.get_member(user)

                # If the member has left the server
                if not owner:
                    continue

                delete = True
                to_delete = []
                value = []
                for i, perso in enumerate(shopping_list_dict[user]):
                    if total_persos >= nb_per_page:
                        break

                    value.append(perso)
                    total_persos += 1
                    to_delete.append(i)
                else:
                    del shopping_list_dict[user]
                    delete = False

                if delete:
                    for i in sorted(to_delete, reverse=True):
                        del shopping_list_dict[user][i]

                embed.add_field(name=f'__{owner.name if not owner.nick else owner.nick}__',
                                value='\n'.join(value), inline=False)

                if total_persos >= 20:
                    break

            shopping_list_pages.append(embed)

        shopping_list_pages = ["No shopping list found..."] if not shopping_list_pages else shopping_list_pages
        paginator = pages.Paginator(pages=shopping_list_pages, show_disabled=True, show_indicator=True)
        await paginator.send(ctx)
