from datetime import datetime
import asyncio
import math

import discord
from discord.ext import commands

from database import DatabaseDeck, DatabasePersonality
from roll import min_until_next_claim

class Profile(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(aliases=['pr'], description='Show the user profile or yours if no user given.')
    async def profile(self, ctx):
        user = ctx.author if not ctx.message.mentions else ctx.message.mentions[0]

        ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, user.id)

        async def send_embed(desc):
            embed = discord.Embed(title=user.name if user.nick is None else user.nick, description=desc)
            embed.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed)

        persos_text = []
        personalities = DatabasePersonality.get().get_multiple_perso_information(ids_deck)
        if personalities:
            for perso in personalities:
                persos_text.append(f'**{perso["name"]}** *{perso["group"]}*')

        persos_text.sort()

        current_page = 1
        nb_per_page = 20
        max_page = math.ceil(len(persos_text) / float(nb_per_page))

        embed = discord.Embed(title=user.name if user.nick is None else user.nick,
                              description='\n'.join([perso for perso in persos_text[(current_page - 1) * nb_per_page:current_page * nb_per_page]]))
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=f'{current_page} \\ {max_page}')
        msg = await ctx.send(embed=embed)

        if max_page > 1:
            # Page handler
            left_emoji = '\U00002B05'
            right_emoji = '\U000027A1'
            await msg.add_reaction(left_emoji)
            await msg.add_reaction(right_emoji)

            def check(reaction, user):
                return user != self.bot.user and (str(reaction.emoji) == left_emoji or str(reaction.emoji) == right_emoji) \
                       and reaction.message.id == msg.id

            timeout = False

            while not timeout:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reaction(left_emoji)
                    await msg.clear_reaction(right_emoji)
                    timeout = True
                else:
                    old_page = current_page
                    if reaction.emoji == left_emoji:
                        current_page = current_page - 1 if current_page > 1 else max_page

                    if reaction.emoji == right_emoji:
                        current_page = current_page + 1 if current_page < max_page else 1

                    await msg.remove_reaction(reaction.emoji, user)

                    # Refresh embed message with the new text
                    if old_page != current_page:
                        embed = discord.Embed(title=user.name if user.nick is None else user.nick,
                                              description='\n'.join([perso for perso in persos_text[(current_page - 1) * nb_per_page:current_page * nb_per_page]]))
                        embed.set_thumbnail(url=user.avatar_url)
                        embed.set_footer(text=f'{current_page} \\ {max_page}')
                        await msg.edit(embed=embed)

    @commands.command(aliases=['tu'], description='Show time before next rolls and claim reset.')
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

        await ctx.send(msg)
