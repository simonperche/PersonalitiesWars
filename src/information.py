import asyncio
import secrets
import math
import datetime

import discord
from discord.ext import commands, pages
from discord.commands import slash_command, Option
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import DatabasePersonality, DatabaseDeck
import utils


class Information(commands.Cog):

    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.send_last_claims_on_servers, CronTrigger(hour=8, minute=0, second=0))
        scheduler.start()

    #### Commands ####

    @slash_command(description='Show information about a personality',
                   guild_ids=utils.get_authorized_guild_ids())
    async def information(self, ctx, name: Option(str, "Pick a name or write yours", autocomplete=utils.personalities_name_searcher),
                          group: Option(str, "Pick a group or write yours", autocomplete=utils.personalities_group_searcher, required=False, default=None)):
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
            await ctx.respond(msg)
            return

        current_image = DatabaseDeck.get().get_perso_current_image(ctx.guild.id, id_perso)
        perso = DatabasePersonality.get().get_perso_information(id_perso, current_image)

        embed = discord.Embed(title=perso['name'], description=perso['group'], colour=secrets.randbelow(0xffffff))

        id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)

        # Counter variables
        total_images = DatabasePersonality.get().get_perso_images_count(id_perso)
        current_image = parse_int(DatabaseDeck().get().get_perso_current_image(ctx.guild.id, id_perso)) + 1

        # Footer have always the picture counter, and eventually the owner info
        text = f'{current_image} \\ {total_images} \n'
        if id_owner:
            owner = ctx.guild.get_member(id_owner)
            if owner:
                text = f'{text}Belongs to {owner.name if not owner.nick else owner.nick}'
                if owner.avatar:
                    embed.set_footer(icon_url=owner.avatar.url, text=text)
                else:
                    embed.set_footer(text=text)
        else:
            embed.set_footer(text=text)

        embed.set_image(url=perso['image'])

        badges_with_perso = DatabaseDeck.get().get_badges_with(ctx.guild.id, id_perso)
        if badges_with_perso:
            embed.add_field(name=f'Badge{"s" if len(badges_with_perso) > 1 else ""}',
                            value='\n'.join([badge['name'] for badge in badges_with_perso]))

        await ctx.respond(embed=embed)
        msg = await ctx.interaction.original_message()

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
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reaction(left_emoji)
                await msg.clear_reaction(right_emoji)
                timeout = True
            else:
                old_image = current_image
                if reaction.emoji == left_emoji:
                    DatabaseDeck.get().decrement_perso_current_image(ctx.guild.id, id_perso)

                if reaction.emoji == right_emoji:
                    DatabaseDeck.get().increment_perso_current_image(ctx.guild.id, id_perso)

                current_image = parse_int(DatabaseDeck().get().get_perso_current_image(ctx.guild.id, id_perso)) + 1
                await msg.remove_reaction(reaction.emoji, user)

                # Refresh embed message with the new picture if changed
                if old_image != current_image:
                    # Redo the query because image link changed
                    image_number = DatabaseDeck.get().get_perso_current_image(ctx.guild.id, id_perso)
                    perso = DatabasePersonality.get().get_perso_information(id_perso, image_number)
                    embed.set_image(url=perso['image'])
                    
                    text = f'{current_image} \\ {total_images} \n'
                    if id_owner and owner:
                        text = f'{text}Belongs to {owner.name if not owner.nick else owner.nick}'
                        if owner.avatar:
                            embed.set_footer(icon_url=owner.avatar.url, text=text)
                        else:
                            embed.set_footer(text=text)
                    else:
                        embed.set_footer(text=text)

                    await msg.edit(embed=embed)

    @slash_command(description='List all personalities with its name',
                   guild_ids=utils.get_authorized_guild_ids())
    async def list(self, ctx, name: str):
        ids = DatabasePersonality.get().get_perso_ids_containing_name(name)

        if not ids:
            await ctx.respond(f'No *{name}* personality found')
            return

        persos_text = []
        personalities = DatabasePersonality.get().get_multiple_perso_information(ids)
        if personalities:
            for perso in personalities:
                persos_text.append(f'**{perso["name"]}** *{perso["group"]}*')

        persos_text.sort()

        nb_per_page = 20
        persos_pages = []

        for i in range(0, len(persos_text), nb_per_page):
            embed = discord.Embed(title=f'*{name}* personality',
                                  description='\n'.join([perso for perso in persos_text[i:i + nb_per_page]]))
            persos_pages.append(embed)

        paginator = pages.Paginator(pages=persos_pages, show_disabled=False, show_indicator=True)
        await paginator.send(ctx)

    @slash_command(description='Show all members of a group',
                   guild_ids=utils.get_authorized_guild_ids())
    async def group(self, ctx, group_name: Option(str, "Pick a group or write yours", autocomplete=utils.personalities_group_searcher)):
        group = DatabasePersonality.get().get_group_members(group_name)

        if not group:
            await ctx.respond(f'No *{group_name}* group found.')
            return

        nb_per_page = 20
        persos_pages = []

        for i in range(0, len(group['members']), nb_per_page):
            embed = discord.Embed(title=f'*{group["name"]}* group',
                                  description='\n'.join([f'**{member}**' for member in group['members'][i:i+nb_per_page]]))
            persos_pages.append(embed)

        paginator = pages.Paginator(pages=persos_pages, show_disabled=False, show_indicator=True)
        await paginator.send(ctx)

    @slash_command(description='Show all groups available',
                   guild_ids=utils.get_authorized_guild_ids())
    async def list_groups(self, ctx):
        groups = DatabasePersonality.get().get_all_groups()

        if not groups:
            await ctx.respond(f'No group found. This is probably an error.')
            return

        nb_per_page = 20
        persos_pages = []

        for i in range(0, len(groups), nb_per_page):
            embed = discord.Embed(title=f'All groups',
                                  description='\n'.join([f'**{group}**' for group in groups[i:i+nb_per_page]]))
            persos_pages.append(embed)

        paginator = pages.Paginator(pages=persos_pages, show_disabled=False, show_indicator=True)
        await paginator.send(ctx)

    @slash_command(description='Show last claims of the last 24h of the current channel.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def last_claims(self, ctx):
        await ctx.defer()
        embed = await self.last_claims_function(ctx.channel)
        await ctx.respond(content='', embed=embed)

    async def send_last_claims_on_servers(self):
        servers = DatabaseDeck.get().get_servers_with_info_and_claims_channels()
        for server in servers:
            guild = self.bot.get_guild(server['id'])
            embed = await self.last_claims_function(guild.get_channel(server['claims_channel']))
            await guild.get_channel(server['information_channel']).send(embed=embed)

    # Get last claims in channel and return an embed
    async def last_claims_function(self, channel: discord.TextChannel):
        yesterday = datetime.datetime.utcnow().today() - datetime.timedelta(days=1)
        claims = []

        async for message in channel.history(limit=None, after=yesterday, oldest_first=True):
            if message.author != self.bot.user:
                continue

            if ' claims ' in message.content and message.content.endswith('!'):
                s = message.content.split(' claims ')
                owner = s[0]
                # Remove '!'
                personality = s[1][:-1]
                claims.append(f'**{personality}** - {owner}')

        embed = discord.Embed(title='Last 24h claims', description='\n'.join(claims) if claims else 'No one has claimed anything...')
        embed.set_footer(text=f'Channel {channel.name}')

        return embed


def parse_int(content):
    try:
        return int(content)
    except ValueError:
        return 0