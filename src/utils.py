from typing import Dict, List, Optional, Union

import discord
from discord.ext import pages

from database import DatabasePersonality, DatabaseDeck


# Set authorized guilds for slash command (return [] for global command - might take up to 1h to register)
def get_authorized_guild_ids():
    return [550631040826343427]


async def personalities_name_searcher(ctx: discord.AutocompleteContext):
    return [perso['name'] for perso in DatabasePersonality.get().get_all_personalities()
            if ctx.value.lower() in perso['name'].lower()]


async def personalities_group_searcher(ctx: discord.AutocompleteContext):
    return [group for group in DatabasePersonality.get().get_all_groups() if ctx.value.lower() in group.lower()]


async def wishlist_name_searcher(ctx: discord.AutocompleteContext):
    ids = DatabaseDeck.get().get_wishlist(ctx.interaction.guild.id, ctx.interaction.user.id)
    personalities = DatabasePersonality.get().get_multiple_perso_information(ids)
    return [perso['name'] for perso in personalities
            if ctx.value.lower() in perso['name'].lower()]


async def deck_name_searcher(ctx: discord.AutocompleteContext):
    ids = DatabaseDeck.get().get_user_deck(ctx.interaction.guild.id, ctx.interaction.user.id)
    personalities = DatabasePersonality.get().get_multiple_perso_information(ids)
    return [perso['name'] for perso in personalities
            if ctx.value.lower() in perso['name'].lower()]


async def badges_name_searcher(ctx: discord.AutocompleteContext):
    badges = DatabaseDeck.get().get_all_badges(ctx.interaction.guild.id)
    return [badge['name'] for badge in badges if ctx.value.lower() in badge['name'].lower()]


class ConfirmView(discord.ui.View):
    def __init__(self, authorized_user: discord.User, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.is_accepted = None
        self.authorized_user = authorized_user

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.is_accepted = True
        button.label = 'Yes (chosen)'
        await self.disable_update_and_stop(interaction)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.is_accepted = False
        button.label = 'No (chosen)'
        await self.disable_update_and_stop(interaction)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.authorized_user:
            await interaction.response.send_message('You cannot answer, you are not the recipient.', ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        await self.disable()

    async def disable_update_and_stop(self, interaction: discord.Interaction):
        await self.disable()
        await interaction.response.edit_message(view=self)
        self.stop()

    async def disable(self):
        for child in self.children:
            child.disabled = True


class PaginatorCustomStartPage(pages.Paginator):
    def __init__(
        self,
        pages: Union[List[str], List[discord.Embed]],
        author_check=True,
        custom_view: Optional[discord.ui.View] = None,
        timeout: Optional[float] = 180.0,
        first_page: int = 0
    ) -> None:
        super().__init__(pages=pages, show_disabled=True, show_indicator=True, author_check=author_check,
                         disable_on_timeout=True, custom_view=custom_view, timeout=timeout)

        if first_page >= len(pages):
            first_page = len(pages) - 1
        elif first_page < 0:
            first_page = 0

        self.current_page = first_page
        self.update_buttons()

    async def respond(self, interaction: discord.Interaction, ephemeral: bool = False):
        """Sends an interaction response or followup with the paginated items.


        Parameters
        ------------
        interaction: :class:`discord.Interaction`
            The interaction associated with this response.
        ephemeral: :class:`bool`
            Choose whether the message is ephemeral or not.

        Returns
        --------
        :class:`~discord.Interaction`
            The message sent with the paginator.
        """
        page = self.pages[self.current_page]
        self.user = interaction.user

        if interaction.response.is_done():
            msg = await interaction.followup.send(
                content=page if isinstance(page, str) else None, embed=page if isinstance(page, discord.Embed) else None, view=self, ephemeral=ephemeral
            )

        else:
            msg = await interaction.response.send_message(
                content=page if isinstance(page, str) else None, embed=page if isinstance(page, discord.Embed) else None, view=self, ephemeral=ephemeral
            )
        if isinstance(msg, (discord.WebhookMessage, discord.Message)):
            self.message = msg
        elif isinstance(msg, discord.Interaction):
            self.message = await msg.original_message()
        return self.message

