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
        perso = DatabasePersonality.get().get_perso_information(id_perso)
        images = DatabasePersonality.get().get_perso_all_images(id_perso)

        id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)
        owner = None
        if id_owner:
            owner = ctx.guild.get_member(id_owner)

        badges_with_perso = DatabaseDeck.get().get_badges_with(ctx.guild.id, id_perso)

        images_pages = []

        for i in range(0, len(images)):
            embed = discord.Embed(title=perso['name'], description=perso['group'], colour=secrets.randbelow(0xffffff))
            if badges_with_perso:
                embed.add_field(name=f'Badge{"s" if len(badges_with_perso) > 1 else ""}',
                                value='\n'.join([badge['name'] for badge in badges_with_perso]))
            if owner:
                text = f'Belongs to {owner.name if not owner.nick else owner.nick}'
                if owner.avatar:
                    embed.set_footer(icon_url=owner.avatar.url, text=text)
                else:
                    embed.set_footer(text=text)

            embed.set_image(url=images[i])

            images_pages.append(embed)

        class SetDefaultButton(discord.ui.View):
            def __init__(self, timeout: int = 180):
                super().__init__(timeout=timeout)
                self.paginator = None

            def set_paginator(self, paginator: utils.PaginatorCustomStartPage):
                self.paginator = paginator

            @discord.ui.button(label="Choose as default image", style=discord.ButtonStyle.green, row=1)
            async def button_default_image(self, button: discord.ui.Button, interaction: discord.Interaction):
                if not self.paginator:
                    await ctx.send(f'Error while setting the image, contact the administrator.', delete_after=5)
                else:
                    DatabaseDeck.get().update_perso_current_image(ctx.guild.id, id_perso, self.paginator.current_page)
                    await ctx.send(f'Set image {self.paginator.current_page+1} as default image.', delete_after=5)

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

        button = SetDefaultButton()
        try:
            current_image_index = images.index(current_image)
        except ValueError:
            current_image_index = 0
        paginator = utils.PaginatorCustomStartPage(pages=images_pages, first_page=current_image_index,
                                                   custom_view=button)
        button.set_paginator(paginator)
        await paginator.respond(ctx)

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