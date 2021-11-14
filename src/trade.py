import asyncio
import string
import secrets

from discord.ext import commands

from database import DatabasePersonality, DatabaseDeck


class Trade(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####
    @commands.command(description='Trade one personality for another.')
    async def trade(self, ctx, user, name, group=None):
        if not ctx.message.mentions:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Please specify a user.')
            return None

        id_perso_give = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso_give:
            return

        user = ctx.message.mentions[0]

        def check_name_group(message):
            param = list(filter(None, map(str.strip, message.content.split('"'))))
            return message.author == user and (not param or 1 <= len(param) <= 2)

        await ctx.send(f'{user.mention}, {ctx.author.mention} wants to trade with you.\n'
                       f'Who do you want to trade for **{name}** ?\n'
                       f'\nType name ["group"] **("" required around group!)**')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check_name_group)
        except asyncio.TimeoutError:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Too late... Give is cancelled.')
            return

        arg = list(filter(None, map(str.strip, msg.content.split('"'))))
        name_receive = arg[0]
        group_receive = [] if len(arg) == 1 else arg[1]

        id_perso_receive = await self.can_give(ctx, user, name_receive, group_receive)
        if not id_perso_receive:
            return

        def check(message):
            return message.author == ctx.author and \
                   (message.content.lower() == 'yes' or message.content.lower() == 'y' or
                    message.content.lower() == 'no' or message.content.lower() == 'n')

        await ctx.send(f'{user.mention} trades **{name_receive}** for **{name}**.\n'
                       f'{ctx.author.mention}, do you accept? (y|yes or n|no)\n')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Too late... Give is cancelled.')
        else:
            if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
                DatabaseDeck.get().give_to(ctx.guild.id, id_perso_give, ctx.author.id, user.id)
                DatabaseDeck.get().give_to(ctx.guild.id, id_perso_receive, user.id, ctx.author.id)
                await ctx.message.add_reaction(u"\u2705")
                await msg.add_reaction(u"\u2705")
            else:
                await ctx.send('Trade is cancelled.')

    @commands.command(description='Give one personality to someone.')
    async def give(self, ctx, user, name, group=None):
        if not ctx.message.mentions:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Please specify a user.')
            return None

        id_perso = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso:
            return

        user = ctx.message.mentions[0]

        def check(message):
            return message.author == user and (message.content.lower() == 'yes' or message.content.lower() == 'y' or
                                               message.content.lower() == 'no' or message.content.lower() == 'n')

        await ctx.send(f'{user.mention}, {ctx.author.mention} wants to give you **{name}**.\n'
                       f'Type y|yes or n|no.')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Too late... Give is cancelled.')
        else:
            if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
                DatabaseDeck.get().give_to(ctx.guild.id, id_perso, ctx.author.id, user.id)
                await ctx.message.add_reaction(u"\u2705")
                await msg.add_reaction(u"\u2705")
            else:
                await ctx.send('Give is cancelled.')

    @commands.command(description='Remove a personality from your deck (can\'t be undone!).')
    async def discard(self, ctx, name, group=None):
        id_perso = await self.can_give(ctx, ctx.author, name, group)
        if not id_perso:
            return

        def check(message):
            return message.author == ctx.author \
                   and message.channel == ctx.message.channel \
                   and (message.content.lower() == 'yes' or message.content.lower() == 'y' or
                        message.content.lower() == 'no' or message.content.lower() == 'n')

        await ctx.send(f'{ctx.author.mention}, are you sure you want to discard **{name}**? (y|yes or n|no)\n')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Discard is cancelled.')
        else:
            if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
                DatabaseDeck.get().give_to(ctx.guild.id, id_perso, ctx.author.id, None)
                await ctx.message.add_reaction(u"\u2705")
                await msg.add_reaction(u"\u2705")
            else:
                await ctx.send('Discard is cancelled.')

    @commands.command(description='Remove all personalities from your deck (can\'t be undone!).')
    async def discard_all(self, ctx):
        letters = string.ascii_letters
        random_string = 'cancel'

        while random_string == 'cancel':
            random_string = ''.join(secrets.choice(letters) for i in range(5))

        def check(message):
            return message.author == ctx.author \
                   and message.channel == ctx.message.channel \
                   and (message.content == random_string or message.content.lower() == 'cancel')

        await ctx.send(f'{ctx.author.mention}, are you sure you want to discard **all your deck**?\n'
                       f'This cannot be undone! Please type *{random_string}* (with case) to confirm '
                       f'or *cancel* to cancel.')
        try:
            msg = await self.bot.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send('Discard is cancelled.')
        else:
            if msg.content.lower() == 'cancel':
                await ctx.message.add_reaction(u"\u274C")
                await ctx.send('Discard is cancelled.')
                return

            ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, ctx.author.id)

            for id_perso in ids_deck:
                DatabaseDeck.get().give_to(ctx.guild.id, id_perso, ctx.author.id, None)

            await ctx.message.add_reaction(u"\u2705")
            await msg.add_reaction(u"\u2705")

    @staticmethod
    async def can_give(ctx, author, name, group=None):
        """Return perso id if the user can give, None otherwise."""
        ## Find perso id
        name = name.strip()

        if group:
            group = group.strip()

        id_perso = None

        if group:
            id_perso = DatabasePersonality.get().get_perso_group_id(name, group)
        else:
            ids = DatabasePersonality.get().get_perso_ids(name)
            if ids:
                id_perso = ids[0]

        if not id_perso:
            msg = f'I searched everywhere for **{name}**'
            if group:
                msg += f' in the group *{group}*'
            msg += ' and I couldn\'t find anything.\nPlease check the command.'
            await ctx.send(msg)
            return None

        # Check if perso belongs to author
        owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)
        if not owner or owner != author.id:
            await ctx.message.add_reaction(u"\u274C")
            await ctx.send(f'You don\'t own **{name}**{" from *" + group + "* " if group else ""}...')
            return None

        return id_perso
