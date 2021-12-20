import discord

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
