from datetime import datetime
import asyncio
import math
from collections import defaultdict

import discord
from discord.ext import commands, pages
from discord.commands import slash_command, Option

from database import DatabaseDeck, DatabasePersonality
from roll import min_until_next_claim
import utils


class Profile(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @slash_command(aliases=['pr'], description='Show the user profile or yours if no user given.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def profile(self, ctx, member: Option(discord.Member, required=False, default=None)):
        profile_owner = member or ctx.author
        id_perso_profile = DatabaseDeck.get().get_id_perso_profile(ctx.guild.id, profile_owner.id)

        image = profile_owner.avatar.url if profile_owner.avatar else None

        if id_perso_profile:
            current_image = DatabaseDeck.get().get_perso_current_image(ctx.guild.id, id_perso_profile)
            perso = DatabasePersonality.get().get_perso_information(id_perso_profile)

            # Show profile's perso only if user owns the personality (might not be the case with trade, give, discard)
            owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, perso['id'])
            if owner and owner == profile_owner.id and current_image:
                image = current_image

        ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, profile_owner.id)

        groups_count = defaultdict(int)  # Default value of 0
        personalities = DatabasePersonality.get().get_multiple_perso_information(ids_deck)
        if personalities:
            for perso in personalities:
                groups_count[perso["group"]] += 1

        # Keep only the 10 most popular groups
        groups = sorted(groups_count.items(), key=lambda item: item[1], reverse=True)[:10]

        # Badges
        owned_badges = []
        badges = DatabaseDeck.get().get_all_badges_with_perso(ctx.guild.id)
        for badge_name in badges:
            if all(id_perso in ids_deck for id_perso in badges[badge_name]):
                owned_badges.append(badge_name)
        badges_embed_msg = 'You don\'t own any badge...'
        if owned_badges:
            badges_embed_msg = '\n'.join(owned_badges)

        embed = discord.Embed(
            title=f'Profile of {profile_owner.name if profile_owner.nick is None else profile_owner.nick}', type='rich')
        embed.description = f'You own {len(ids_deck)} personalit{"ies" if len(ids_deck) > 1 else "y"}!'
        embed.add_field(name='Badges', value=badges_embed_msg)
        if groups:
            embed.add_field(name='Most owned groups',
                            value='\n'.join([f'*{group[0].capitalize()}* ({group[1]})' for group in groups]))
        if image:
            embed.set_thumbnail(url=image)

        await ctx.respond(embed=embed)

    @slash_command(description='Show the user deck or yours if no user given.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def deck(self, ctx, member: Option(discord.Member, required=False, default=None)):
        deck_owner = member or ctx.author

        ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, deck_owner.id)

        persos_text = []
        personalities = DatabasePersonality.get().get_multiple_perso_information(ids_deck)
        if personalities:
            for perso in personalities:
                persos_text.append(f'**{perso["name"]}** *{perso["group"]}*')

        persos_text.sort()

        nb_per_page = 20
        persos_pages = []

        for i in range(0, len(persos_text), nb_per_page):
            embed = discord.Embed(title=deck_owner.name if deck_owner.nick is None else deck_owner.nick,
                                  description='\n'.join([perso for perso in persos_text[i:i + nb_per_page]]))
            if deck_owner.avatar:
                embed.set_thumbnail(url=deck_owner.avatar.url)
            persos_pages.append(embed)

        paginator = pages.Paginator(pages=persos_pages, show_disabled=False, show_indicator=True)
        await paginator.send(ctx)

    @slash_command(description='Set the profile displayed personality.\n'
                               'You can leave name blank to remove the current personality.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def set_perso_profile(self, ctx, name: Option(str, 'Pick a name or write yours',
                                                        autocomplete=utils.deck_name_searcher),
                                group: Option(str, 'Pick a group or write yours',
                                              autocomplete=utils.personalities_group_searcher, required=False,
                                              default=None)):
        if name is None:
            DatabaseDeck.get().set_id_perso_profile(ctx.guild.id, ctx.author.id, None)
            await ctx.respond('I removed your profile\'s personality.')
            return

        name = name.strip()

        if group:
            group = group.strip()

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            await ctx.respond(f'Personality **{name}**{" from *" + group + "* " if group else ""} not found.')
            return

        owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)
        if not owner or owner != ctx.author.id:
            await ctx.respond(f'You don\'t own **{name}**{" from *" + group + "* " if group else ""}...')
            return None

        DatabaseDeck.get().set_id_perso_profile(ctx.guild.id, ctx.author.id, id_perso)
        await ctx.respond(f'Set your perso profile to {name} {group if group else ""}')

    @slash_command(description='Show time before next rolls and claim reset.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def time(self, ctx):
        next_claim = min_until_next_claim(ctx.guild.id, ctx.author.id)

        username = ctx.author.name if ctx.author.nick is None else ctx.author.nick

        msg = f'{username}, you '
        if next_claim == 0:
            msg += 'can claim right now!'
        else:
            time = divmod(next_claim, 60)
            msg += 'can\'t claim for another **' + \
                   (str(time[0]) + 'h ' if time[0] != 0 else '') + f'{str(time[1])} min**.'

        user_nb_rolls = DatabaseDeck.get().get_nb_rolls(ctx.guild.id, ctx.author.id)
        max_rolls = DatabaseDeck.get().get_rolls_per_hour(ctx.guild.id)

        last_roll = DatabaseDeck.get().get_last_roll(ctx.guild.id, ctx.author.id)
        if not last_roll:
            user_nb_rolls = 0
        else:
            last_roll = datetime.strptime(last_roll, '%Y-%m-%d %H:%M:%S')
            now = datetime.now()

            # If a new hour began
            if now.date() != last_roll.date() or (now.date() == last_roll.date() and now.hour != last_roll.hour):
                user_nb_rolls = 0

        msg += f'\nYou have **{max_rolls - user_nb_rolls}** rolls left.\n' \
               f'Next rolls reset in **{60 - datetime.now().minute} min**.'

        await ctx.respond(msg)
