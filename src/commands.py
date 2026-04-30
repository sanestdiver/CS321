import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from book_api import search_google_books
from book_utils import is_isbn
from embeds import (
    create_result_embed,
    create_placeholder_embed,
    create_help_embed,
)
from views import BookSelectView


# registers all bot commands
def setup_commands(bot: commands.Bot):

    # sends help message with instructions and examples
    @bot.tree.command(name="help", description="How to use the book finder bot")
    async def help_command(interaction: discord.Interaction):
        embed = create_help_embed()
        await interaction.response.send_message(embed=embed)

    # placeholder command for renting books
    @bot.tree.command(name="rent", description="Find books to rent")
    async def rent(interaction: discord.Interaction):
        embed = create_placeholder_embed("📦 Renting Coming Soon")
        await interaction.response.send_message(embed=embed)

    # placeholder command for combined buy and rent listings
    @bot.tree.command(name="all", description="View buy and rent listings together")
    async def all_command(interaction: discord.Interaction):
        embed = create_placeholder_embed("📦 Full Listings Coming Soon")
        await interaction.response.send_message(embed=embed)

    # searches for books by title or isbn
    @bot.tree.command(name="buy", description="Find books to buy by title or ISBN")
    @app_commands.describe(query="Enter a book title or ISBN")
    async def buy(interaction: discord.Interaction, query: str):
        try:
            # delays response while the bot searches
            await interaction.response.defer(thinking=True)

        except discord.NotFound:
            # handles expired interaction (e.g. user takes too long to confirm edition)
            print("Interaction expired before defer.")
            return

        except discord.InteractionResponded:
            # ignores if interaction was already responded to (e.g. user confirms edition after defer)
            pass

        try:
            # opens api session and searches google books
            async with aiohttp.ClientSession() as session:
                books = await search_google_books(session, query, max_results=5)

            # handles no search results
            if not books:
                embed = discord.Embed(
                    title="❌ No results found",
                    description=f"I could not find anything for **{query}**.",
                    color=discord.Color.red(),
                )
                embed.set_footer(text="Try another title or use an ISBN.")
                await interaction.followup.send(embed=embed)
                return

            # if query is isbn show results directly
            if is_isbn(query):
                embeds = []

                # build one embed for each book result
                for index, book_item in enumerate(books, start=1):
                    is_cheapest = index == 1
                    embeds.append(
                        create_result_embed(
                            book_item,
                            query,
                            index,
                            is_cheapest,
                        )
                    )

                await interaction.followup.send(embeds=embeds)
                return

            # if query is title ask user to confirm edition
            confirm_embed = discord.Embed(
                title="📚 Confirm Book Edition",
                description="Use the dropdown below to confirm the correct book edition.",
                color=discord.Color.blurple(),
            )
            confirm_embed.set_footer(text="Select a book to continue.")

            # creates dropdown view for confirming book edition
            view = BookSelectView(books, interaction.user, query)
            await interaction.followup.send(embed=confirm_embed, view=view)

        except Exception as error:
            # logs buy command errors
            print(f"Error in /buy: {error}")

            try:
                # sends fallback error message
                await interaction.followup.send(
                    "Something went wrong while searching for that book."
                )
            except Exception:
                pass

    # handles slash command errors
    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        print(f"App command error: {error}")

        try:
            # sends error message based on response state
            if interaction.response.is_done():
                await interaction.followup.send(
                    "There was an error running that command."
                )
            else:
                await interaction.response.send_message(
                    "There was an error running that command.",
                    ephemeral=True,
                )
        except Exception:
            pass