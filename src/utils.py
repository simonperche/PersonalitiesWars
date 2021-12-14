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
