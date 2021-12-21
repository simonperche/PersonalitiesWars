import secrets
import asyncio
from datetime import datetime

import discord
from discord.ext import commands

from database import DatabasePersonality, DatabaseDeck


class Roll(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @commands.command(description='Roll a random idom and get the possibility to claim it.')
    async def roll(self, ctx):
        minutes = min_until_next_roll(ctx.guild.id, ctx.author.id)
        if minutes != 0:
            await ctx.send(f'You cannot roll right now. The next roll reset is in {minutes} minutes.')
            return

        perso = None
        id_perso = None

        msg_embed = ''

        while not perso:
            id_perso = DatabasePersonality.get().get_random_perso_id()
            perso = DatabasePersonality.get().get_perso_information(id_perso)

        # Update roll information in database
        DatabaseDeck.get().update_last_roll(ctx.guild.id, ctx.author.id)
        user_nb_rolls = DatabaseDeck.get().get_nb_rolls(ctx.guild.id, ctx.author.id)
        DatabaseDeck.get().set_nb_rolls(ctx.guild.id, ctx.author.id, user_nb_rolls + 1)

        max_rolls = DatabaseDeck.get().get_rolls_per_hour(ctx.guild.id)
        if max_rolls - user_nb_rolls - 1 == 2:
            msg_embed += f'{ctx.author.name if ctx.author.nick is None else ctx.author.nick}, 2 uses left.\n'

        # Get badges information
        badges_with_perso = DatabaseDeck.get().get_badges_with(ctx.guild.id, id_perso)
        if badges_with_perso:
            msg_embed += f'**Required for {",".join([badge["name"] for badge in badges_with_perso])}' \
                         f' badge{"" if len(badges_with_perso) == 1 else "s"}!**\n'

        current_image = DatabaseDeck.get().get_perso_current_image(ctx.guild.id, id_perso)

        embed = discord.Embed(title=perso['name'], description=perso['group'], colour=secrets.randbelow(0xffffff))

        if current_image:
            embed.set_image(url=current_image)

        id_owner = DatabaseDeck.get().perso_belongs_to(ctx.guild.id, id_perso)
        if id_owner:
            owner = ctx.guild.get_member(id_owner)

            # Could be None if the user left the server
            if owner:
                text = f'Belongs to {owner.name if not owner.nick else owner.nick}'
                if owner.avatar:
                    embed.set_footer(icon_url=owner.avatar.url, text=text)
                else:
                    embed.set_footer(text=text)

        # Mention users if they wish for this personality
        id_members = DatabaseDeck.get().get_wished_by(ctx.guild.id, id_perso)

        wish_msg = ''
        for id_member in id_members:
            member = ctx.guild.get_member(id_member)
            # Could be None if the user left the server
            if member:
                wish_msg += f'{member.mention} '

        if wish_msg:
            msg_embed += f'Wished by {wish_msg}'

        class ClaimButton(discord.ui.View):
            def __init__(self, timeout: int):
                super().__init__(timeout=timeout)
                self.is_claimed = False
                self.user_claim = None

            @discord.ui.button(label="Claim", emoji='💕', style=discord.ButtonStyle.green)
            async def claim(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.user_claim = interaction.user
                self.is_claimed = True
                self.disable()

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                time_until_claim = min_until_next_claim(interaction.guild.id, interaction.user.id)
                if time_until_claim != 0:
                    time = divmod(time_until_claim, 60)
                    cant_claiming_username = interaction.user.name if interaction.user.nick is None else interaction.user.nick
                    await interaction.response.send_message(f'{cant_claiming_username}, you can\'t claim right now. '
                                                            f'Please wait **{str(time[0]) + "h " if time[0] != 0 else ""}{str(time[1])} min**.')
                    return False

                return True

            def disable(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

        claim_timeout = DatabaseDeck.get().get_server_configuration(ctx.guild.id)["time_to_claim"]
        claim_button_view = ClaimButton(timeout=claim_timeout)

        # Cannot claim if perso already claim
        if id_owner:
            await ctx.send(msg_embed, embed=embed)
            return

        msg = await ctx.send(msg_embed, embed=embed, view=claim_button_view)
        await claim_button_view.wait()

        # Timeout
        if not claim_button_view.is_claimed:
            claim_button_view.disable()
            await msg.edit(view=claim_button_view)
        else:
            user = claim_button_view.user_claim
            username = user.name if user.nick is None else user.nick

            DatabaseDeck.get().add_to_deck(ctx.guild.id, perso['id'], user.id)
            await ctx.send(f'{username} claims {perso["name"]}!')

            if user.avatar:
                embed.set_footer(icon_url=user.avatar.url, text=f'Belongs to {username}')
            else:
                embed.set_footer(text=f'Belongs to {username}')
            await msg.edit(embed=embed, view=claim_button_view)

            if badges_with_perso:
                ids_deck = DatabaseDeck.get().get_user_deck(ctx.guild.id, user.id)
                msg_badges_progression = ''
                for badge in badges_with_perso:
                    perso_in_badge = DatabaseDeck.get().get_perso_in_badge(badge['id'])
                    count = sum([id_perso in ids_deck for id_perso in perso_in_badge])
                    nb_perso = len(perso_in_badge)
                    if perso['id'] in perso_in_badge and count == nb_perso:
                        await ctx.send(f'**{user.mention}, you have just unlocked {badge["name"]} badge!**')
                    msg_badges_progression += f'{badge["name"]} {count}/{nb_perso}\n'
                badge_embed = discord.Embed(title=f'Badges progression with {perso["name"]}',
                                            description=msg_badges_progression)
                await ctx.send(embed=badge_embed)


#### Utilities functions ####

def min_until_next_claim(id_server, id_user):
    """Return minutes until next claim (0 if the user can claim now)."""
    last_claim = DatabaseDeck.get().get_last_claim(id_server, id_user)

    time_until_claim = 0

    if last_claim:
        claim_interval = DatabaseDeck.get().get_server_configuration(id_server)['claim_interval']
        date_last_claim = datetime.strptime(last_claim, '%Y-%m-%d %H:%M:%S')
        minute_since_last_claim = int(divmod((datetime.now() - date_last_claim).total_seconds(), 60)[0])

        if minute_since_last_claim < claim_interval:
            time_until_claim = claim_interval - minute_since_last_claim

    return time_until_claim


def min_until_next_roll(id_server, id_user):
    """Return minutes until next roll (0 if the user can roll now)."""
    last_roll = DatabaseDeck.get().get_last_roll(id_server, id_user)

    if not last_roll:
        return 0

    last_roll = datetime.strptime(last_roll, '%Y-%m-%d %H:%M:%S')
    now = datetime.now()

    # If a new hour began
    if now.date() != last_roll.date() or (now.date() == last_roll.date() and now.hour != last_roll.hour):
        DatabaseDeck.get().set_nb_rolls(id_server, id_user, 0)
        return 0

    max_rolls = DatabaseDeck.get().get_rolls_per_hour(id_server)
    user_nb_rolls = DatabaseDeck.get().get_nb_rolls(id_server, id_user)

    if user_nb_rolls < max_rolls:
        return 0
    else:
        return 60 - now.minute
