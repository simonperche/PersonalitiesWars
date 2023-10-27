import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from database import DatabasePersonality
import utils


class PersonalitiesHandler(commands.Cog):
    def __init__(self, bot):
        """Initial the cog with the bot."""
        self.bot = bot

    #### Commands ####

    @slash_command(description='Add a personality.',
                   guild_ids=utils.get_authorized_guild_ids())
    async def add_personality(self, ctx, name: Option(str, "The name"),
                              group: Option(str, "Group of the personality",
                                            autocomplete=utils.personalities_group_searcher),
                              image_url: str):
        name = name.strip()

        id_group = DatabasePersonality.get().get_group_id(group)

        if not id_group:
            await ctx.respond(f'Group **{name}** not found.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        DatabasePersonality.get().add_personality(name, id_group, image_url)
        # Green mark
        await ctx.respond(f'{name} in the group {group} has been added.')
        msg = await ctx.interaction.original_message()
        await msg.add_reaction(u"\u2705")

    @slash_command(description='Remove a personality (can\'t be undone!).',
                   guild_ids=utils.get_authorized_guild_ids())
    async def remove_personality(self, ctx,
                           name: Option(str, "Pick a name",
                                        autocomplete=utils.personalities_name_searcher),
                           group: Option(str, "Group of the personality",
                                         autocomplete=utils.personalities_group_searcher)):
        name = name.strip()

        id_perso = DatabasePersonality.get().get_perso_group_id(name, group)

        if not id_perso:
            await ctx.respond(f'Personality **{name}** in the group *{group}* not found.')
            msg = await ctx.interaction.original_message()
            await msg.add_reaction(u"\u274C")
            return

        await ctx.respond('**Danger zone!** This action cannot be undone. '
                          'The personality will be removed from deck, wishlist, shopping list...')

        accept_view = utils.ConfirmView(ctx.author)
        msg = await ctx.send(f'{ctx.author.mention}, are you sure you want to delete **{name}**?',
                             view=accept_view)
        await accept_view.wait()

        # Timeout
        if accept_view.is_accepted is None:
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u274C")
            await ctx.send('Timeout : discard is cancelled.')
            await msg.edit(view=accept_view)
        elif accept_view.is_accepted:
            DatabasePersonality.get().remove_personality(id_perso)
            original_msg = await ctx.interaction.original_message()
            await original_msg.add_reaction(u"\u2705")
            await msg.add_reaction(u"\u2705")
        else:
            await ctx.send('Discard is cancelled.')
