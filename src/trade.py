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
        # Events for blocking the trade while the second member chose a personality
        # Contains id_member: {event: blocking_event, id_perso: id_perso}
        self.events = {}

    #### Commands ####
    @slash_command(description='Trade one personality for another.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def trade(self, ctx, user: Option(discord.Member),
                    name: Option(str, 'Pick a personality', autocomplete=utils.deck_name_searcher),
                    group: Option(str, 'Pick a group or write yours',
                                  autocomplete=utils.personalities_group_searcher, required=False, default=None)):
        key = f'{ctx.guild.id}{user.id}'
        if key in self.events.keys():
            await ctx.respond(f'{user.name if not user.nick else user.nick} is currently in a trade. '
                              f'Please wait and retry...')
            return

        await ctx.respond('Let\'s trade!')
        id_perso_give = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso_give:
            return

        await ctx.send(f'{user.mention}, {ctx.author.mention} wants to trade with you.\n'
                       f'Who do you want to trade for **{name}** ?\n'
                       f'Use /{self.rtrade.name} command to answer.')

        event = asyncio.Event()
        self.events[key] = {'event': event, 'id_perso': None}

        is_timeout = not await utils.event_wait(event=event, timeout=30)
        id_perso_receive = self.events[key]['id_perso']

        del self.events[key]

        if is_timeout:
            await ctx.send('Too late... Give is cancelled.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        perso_receive = DatabasePersonality.get().get_perso_information(id_perso_receive)

        accept_view = utils.ConfirmView(ctx.author)
        msg = await ctx.send(f'{user.mention} trades **{perso_receive["name"]}** for **{name}**.\n'
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

    @slash_command(description='Choose a personality for the current trade',
                   guild_ids=utils.get_authorized_guild_ids())
    async def rtrade(self, ctx, name: Option(str, 'Pick a personality', autocomplete=utils.deck_name_searcher),
                     group: Option(str, 'Pick a group or write yours',
                                   autocomplete=utils.personalities_group_searcher, required=False, default=None)):
        key = f'{ctx.guild.id}{ctx.interaction.user.id}'
        current_trades_members = self.events.keys()
        if key not in current_trades_members:
            await ctx.respond('You have no trade in progress. '
                              'Someone has to start a trade with you using /trade first.', ephemeral=True)
            return

        await ctx.defer()
        id_perso = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso:
            await ctx.respond(content=f'The trade is **not** canceled. '
                                      f'Please indicate a new personality using /{self.rtrade.name}.')
            return

        self.events[key]['id_perso'] = id_perso
        self.events[key]['event'].set()

        await ctx.respond(f'{name}{" - " + group if group else ""}')

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
            msg += ' and I couldn\'t find anything.'
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
