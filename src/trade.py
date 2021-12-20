import asyncio
import string
import secrets

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from database import DatabasePersonality, DatabaseDeck
import utils


class Trade(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####
    @slash_command(description='Trade one personality for another.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def trade(self, ctx, user: Option(discord.Member),
                    name: Option(str, 'Pick a personality', autocomplete=utils.deck_name_searcher),
                    group: Option(str, 'Pick a group or write yours',
                                  autocomplete=utils.personalities_group_searcher, required=False, default=None)):
        await ctx.respond('Let\'s trade!')
        id_perso_give = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso_give:
            return

        def check_name_group(message):
            param = list(filter(None, map(str.strip, message.content.split('"'))))
            return message.author == user and (not param or 1 <= len(param) <= 2)

        await ctx.send(f'{user.mention}, {ctx.author.mention} wants to trade with you.\n'
                       f'Who do you want to trade for **{name}** ?\n'
                       f'\nType name ["group"] **("" required around group!)**')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check_name_group)
        except asyncio.TimeoutError:
            await ctx.send('Too late... Give is cancelled.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        arg = list(filter(None, map(str.strip, msg.content.split('"'))))
        name_receive = arg[0]
        group_receive = [] if len(arg) == 1 else arg[1]

        id_perso_receive = await self.can_give(ctx, user, name_receive, group_receive)
        if not id_perso_receive:
            return

        accept_view = utils.ConfirmView(ctx.author)
        msg = await ctx.send(f'{user.mention} trades **{name_receive}** for **{name}**.\n'
                             f'{ctx.author.mention}, do you accept?', view=accept_view)
        await accept_view.wait()

        # Timeout
        if accept_view.is_accepted is None:
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u274C")
            await ctx.send('Too late... Give is cancelled.')
            await msg.add_reaction(u"\u274C")
            await msg.edit(view=accept_view)
        elif accept_view.is_accepted:
            DatabaseDeck.get().give_to(ctx.guild.id, id_perso_give, ctx.author.id, user.id)
            DatabaseDeck.get().give_to(ctx.guild.id, id_perso_receive, user.id, ctx.author.id)
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u2705")
            await msg.add_reaction(u"\u2705")
        else:
            await ctx.send('Trade is cancelled.')

    @slash_command(description='Give one personality to someone.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def give(self, ctx, user: Option(discord.Member),
                   name: Option(str, 'Pick a personality', autocomplete=utils.deck_name_searcher),
                   group: Option(str, 'Pick a group or write yours',
                                 autocomplete=utils.personalities_group_searcher, required=False, default=None)):
        await ctx.respond('Let\'s give!')
        id_perso = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso:
            return

        accept_view = utils.ConfirmView(user)
        msg = await ctx.send(f'{user.mention}, {ctx.author.mention} wants to give you **{name}**.', view=accept_view)
        await accept_view.wait()

        # Timeout
        if accept_view.is_accepted is None:
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u274C")
            await ctx.send('Too late... Give is cancelled.')
            await msg.edit(view=accept_view)
        elif accept_view.is_accepted:
            DatabaseDeck.get().give_to(ctx.guild.id, id_perso, ctx.author.id, user.id)
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u2705")
            await msg.add_reaction(u"\u2705")
        else:
            await ctx.send('Give is cancelled.')

    @slash_command(description='Remove a personality from your deck (can\'t be undone!).',
                   guild_ids=utils.get_authorized_guild_ids())
    async def discard(self, ctx, name: Option(str, 'Pick a personality', autocomplete=utils.deck_name_searcher),
                      group: Option(str, 'Pick a group or write yours',
                                    autocomplete=utils.personalities_group_searcher, required=False, default=None)):
        await ctx.respond('**Danger zone!** This action cannot be undone.')
        id_perso = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso:
            return

        accept_view = utils.ConfirmView(ctx.author)
        msg = await ctx.send(f'{ctx.author.mention}, are you sure you want to discard **{name}**?',
                             view=accept_view)
        await accept_view.wait()

        # Timeout
        if accept_view.is_accepted is None:
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u274C")
            await ctx.send('Timeout : discard is cancelled.')
            await msg.edit(view=accept_view)
        elif accept_view.is_accepted:
            DatabaseDeck.get().give_to(ctx.guild.id, id_perso, ctx.author.id, None)
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u2705")
            await msg.add_reaction(u"\u2705")
        else:
            await ctx.send('Discard is cancelled.')

    @slash_command(description='Remove all personalities from your deck (can\'t be undone!).',
                   guild_ids=utils.get_authorized_guild_ids())
    async def discard_all(self, ctx):
        await ctx.respond('**Danger zone!** This action **really** cannot be undone.')

        letters = string.ascii_letters
        random_string = 'cancel'

        while random_string == 'cancel':
            random_string = ''.join(secrets.choice(letters) for i in range(5))

        def check(message):
            return message.author == ctx.author \
                   and message.channel == ctx.interaction.channel \
                   and (message.content == random_string or message.content.lower() == 'cancel')

        await ctx.send(f'{ctx.author.mention}, are you sure you want to discard **all your deck**?\n'
                       f'This cannot be undone! Please type *{random_string}* (with case) to confirm '
                       f'or *cancel* to cancel.')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u274C")
            await ctx.send('Discard all is cancelled.')
        else:
            if msg.content.lower() == 'cancel':
                original_msg = await ctx.interaction.original_message()
                await original_msg.add_reaction(u"\u274C")
                await ctx.send('Discard all is cancelled.')
                return

            ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, ctx.author.id)

            for id_perso in ids_deck:
                DatabaseDeck.get().give_to(ctx.guild.id, id_perso, ctx.author.id, None)

            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u2705")
            await msg.add_reaction(u"\u2705")

    @staticmethod
    async def can_give(ctx, author, name, group=None):
        """Return perso id if the user can give, None otherwise."""
        name = name.strip()

        if group:
            group = group.strip()

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            id_perso = DatabasePersonality.get().get_perso_id(name)

        if not id_perso:
            msg = f'I searched everywhere for **{name}**'
            if group:
                msg += f' in the group *{group}*'
            msg += ' and I couldn\'t find anything.\nPlease check the command.'
            await ctx.send(msg)
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return None

        # Check if perso belongs to author
        owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)
        if not owner or owner != author.id:
            await ctx.send(f'You don\'t own **{name}**{" from *" + group + "* " if group else ""}...')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return None

        return id_perso
