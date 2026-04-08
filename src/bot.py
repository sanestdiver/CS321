import os
import re
import random
import urllib.parse
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load values from the .env file
load_dotenv()

# Pull the bot token from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Google Books API endpoint
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

# Standard Discord bot setup with command prefix and intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def clean_isbn(query: str) -> str:
    # ISBN parsing and cleanup - remove spaces and dashes so we can check if it's a valid ISBN
    return re.sub(r"[\s-]", "", query)


def is_isbn(query: str) -> bool:
    # Check whether the user input is a valid 10-digit or 13-digit ISBN
    cleaned = clean_isbn(query)
    return bool(re.fullmatch(r"(\d{10}|\d{13})", cleaned))


def build_goodreads_link(title: str) -> str:
    # Make a Goodreads search link using the book title
    return f"https://www.goodreads.com/search?q={urllib.parse.quote(title)}"


def build_bookscouter_link(title: str, isbn: str | None) -> str:
    # Use ISBN if we have it otherwise fall back to title search for BookScouter link since it can search by either
    search_value = isbn if isbn else title
    return f"https://bookscouter.com/search?query={urllib.parse.quote(search_value)}"


def extract_isbn(volume_info: dict) -> str | None:
    # Google Books may return multiple identifiers,so try ISBN-13 first, then ISBN-10
    identifiers = volume_info.get("industryIdentifiers", [])

    for ident in identifiers:
        if ident.get("type") == "ISBN_13":
            return ident.get("identifier")

    for ident in identifiers:
        if ident.get("type") == "ISBN_10":
            return ident.get("identifier")

    # If no ISBN exists, return None
    return None


def generate_fake_price(seed_value: str) -> float:
    # Generate a repeatable fake price for demo purposes 
    # TODO - in a real implementation, we would want to pull real prices from an API like Amazon or BookScouter instead of generating fake ones
    # CONSIDER APIs such as Amazon Product Advertising API, BookScouter API, or scraping retailer websites for real price data instead of generating fake prices
    # Same seed = same fake price each time
    seeded_random = random.Random(seed_value)
    return round(seeded_random.uniform(25, 120), 2)


def get_numeric_price(book: dict) -> float:
    # Helper for sorting books from cheapest to most expensive
    return book["price_value"]


async def search_google_books(session: aiohttp.ClientSession, query: str) -> list[dict]:
    # If the user entered an ISBN, search by ISBN
    # Otherwise search by title
    if is_isbn(query):
        q = f"isbn:{clean_isbn(query)}"
    else:
        q = f"intitle:{query}"

    params = {
        "q": q,
        "maxResults": 5,
        "printType": "books",
        "key": GOOGLE_API_KEY
    }

    # Send request to Google Books API
    async with session.get(GOOGLE_BOOKS_URL, params=params) as response:
        if response.status != 200:
            return []

        data = await response.json()

    items = data.get("items", [])
    books = []

    # Pull out the fields we care about for each result
    # May have to change new API fields if Google Books updates their response structure in the future
    # In a real implementation, we would want to add error handling here in case the API response structure changes or certain fields are missing
    for item in items:
        volume_info = item.get("volumeInfo", {})
        sale_info = item.get("saleInfo", {})

        title = volume_info.get("title", "Unknown Title")
        authors = ", ".join(volume_info.get("authors", ["Unknown Author"]))
        published = volume_info.get("publishedDate", "Unknown")
        description = volume_info.get("description", "No description available.")
        page_count = volume_info.get("pageCount", "Unknown")
        categories = ", ".join(volume_info.get("categories", ["Unknown"]))
        thumbnail = volume_info.get("imageLinks", {}).get("thumbnail")
        info_link = volume_info.get("infoLink")
        isbn = extract_isbn(volume_info)

        # Try to get the real price from Google Books
        retail_price = sale_info.get("retailPrice", {})
        amount = retail_price.get("amount")
        currency = retail_price.get("currencyCode")

        # Use ISBN as the seed if possible so the fake price stays consistent
        seed_value = isbn if isbn else title

        if amount is not None and currency:
            # Real price exists
            display_price = f"{currency} {amount}"
            price_value = float(amount)
            price_is_estimated = False
        else:
            # No real price found, so generate a fake demo price
            # in a real implementation, we would want to pull real prices from an API like Amazon or BookScouter instead of generating fake ones
            # if no price is available from Google Books, we could also consider showing "Price not available" instead of generating a fake price, depending on the use case and user expectations
            # for demo purposes, we will generate a fake price so that the sorting and price display features of the bot can still be showcased even without real price data
            fake_price = generate_fake_price(seed_value)
            display_price = f"${fake_price} (estimated)"
            price_value = fake_price
            price_is_estimated = True

        # Save all useful book info in one dictionary
        # In a real implementation, we would want to add error handling here in case certain fields are missing from the API response
        books.append({
            "title": title,
            "authors": authors,
            "published": published,
            "description": description,
            "page_count": page_count,
            "categories": categories,
            "thumbnail": thumbnail,
            "info_link": info_link,
            "isbn": isbn,
            "goodreads": build_goodreads_link(title),
            "bookscouter": build_bookscouter_link(title, isbn),
            "price": display_price,
            "price_value": price_value,
            "price_is_estimated": price_is_estimated
        })

    # Sort results so the cheapest book shows first
    books.sort(key=get_numeric_price)
    return books


def create_result_embed(book: dict, query: str, index: int, is_cheapest: bool) -> discord.Embed:
    # Show ISBN if available, otherwise N/A
    # In a real implementation, we would want to handle cases where the ISBN might be missing or malformed more formally
    isbn_text = book["isbn"] if book["isbn"] else "N/A"

    # emebed cleanup
    short_description = book["description"]
    if len(short_description) > 220:
        short_description = short_description[:217] + "..."

    # Add a badge to the cheapest option - just a neat little feature to make it easy for users to spot the lowest price in the results
    # can remove later or change to a 1-5 numbering system if we want to be more neutral 
    title_prefix = "🏷️ Cheapest Option • " if is_cheapest else ""
    embed_title = f"{title_prefix}{index}. {book['title']}"

    # Create the embed
    embed = discord.Embed(
        title=embed_title,
        description=short_description,
        color=discord.Color.gold() if is_cheapest else discord.Color.light_grey()
    )

    # Add book details
    embed.add_field(name="Search", value=query, inline=False)
    embed.add_field(name="Author(s)", value=book["authors"], inline=False)
    embed.add_field(name="Published", value=book["published"], inline=True)
    embed.add_field(name="ISBN", value=isbn_text, inline=True)
    embed.add_field(name="Pages", value=str(book["page_count"]), inline=True)
    embed.add_field(name="Category", value=book["categories"], inline=False)
    embed.add_field(name="💰 Price", value=book["price"], inline=False)

    # Build useful links section
    links = []
    if book["info_link"]:
        links.append(f"[Google Books]({book['info_link']})")
    links.append(f"[Goodreads]({book['goodreads']})")
    links.append(f"[BookScouter]({book['bookscouter']})")

    embed.add_field(name="Links", value=" | ".join(links), inline=False)

    # Add thumbnail if Google Books provides one
    if book["thumbnail"]:
        embed.set_thumbnail(url=book["thumbnail"])

    # Footer explains whether the price is real or estimated
    if is_cheapest:
        embed.set_footer(text="Lowest priced result shown for this search")
    elif book["price_is_estimated"]:
        embed.set_footer(text="Estimated demo price")
    else:
        embed.set_footer(text="Price from Google Books when available")

    return embed


@bot.event
async def on_ready():
    # Runs when the bot successfully logs in
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}")
        print(f"Synced {len(synced)} commands")
    except Exception as error:
        print(f"Sync failed: {error}")


@bot.tree.command(name="help", description="How to use the book finder bot")
async def help_command(interaction: discord.Interaction):
    # Creates a help message for users
    # Standard tutorial style help command that explains how to use the bot and what features it has
    embed = discord.Embed(
        title="📚 Book Finder Help",
        description="Search books by title or ISBN and view results sorted by cheapest price first.",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="Search by title",
        value="`/book query:Winnable`",
        inline=False
    )

    embed.add_field(
        name="Search by ISBN",
        value="`/book query:9780735211292`",
        inline=False
    )

    embed.add_field(
        name="What you get",
        value=(
            "- Top 5 results\n"
            "- Each result in its own box\n"
            "- Cheapest result gets a badge\n"
            "- Real Google Books price if available\n"
            "- Estimated demo price otherwise\n"
            "- Google Books, Goodreads, and BookScouter links"
        ),
        inline=False
    )

    embed.set_footer(text="Results are sorted cheapest first.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="book", description="Search for a book by title or ISBN")
@app_commands.describe(query="Enter a book title or ISBN")
async def book(interaction: discord.Interaction, query: str):
    # Main slash command users will run
    # consider adding /rent for later modes in future
    try:
        # Defer first so Discord knows the bot is working
        await interaction.response.defer(thinking=True)
    except discord.NotFound:
        # This happens if the interaction expired before the bot responded
        print("Interaction expired before defer.")
        return
    except discord.InteractionResponded:
        # Ignore this if Discord already considers the interaction handled
        pass

    try:
        # Open an HTTP session and search Google Books
        async with aiohttp.ClientSession() as session:
            books = await search_google_books(session, query)

        # If nothing came back, tell the user
        if not books:
            embed = discord.Embed(
                title="❌ No results found",
                description=f"I could not find anything for **{query}**.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Try another title or use an ISBN.")
            await interaction.followup.send(embed=embed)
            return

        # Build one embed per book result
        embeds = []
        for index, book_item in enumerate(books, start=1):
            is_cheapest = index == 1
            embeds.append(create_result_embed(book_item, query, index, is_cheapest))

        # Send all embeds back to the user
        await interaction.followup.send(embeds=embeds)

    except Exception as error:
        print(f"Error in /book: {error}")
        try:
            await interaction.followup.send("Something went wrong while searching for that book.")
        except Exception:
            pass


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    # Catches any errors that occur during app command processing and logs them
    print(f"App command error: {error}")

    try:
        if interaction.response.is_done():
            await interaction.followup.send("There was an error running that command.")
        else:
            await interaction.response.send_message(
                "There was an error running that command.",
                ephemeral=True
            )
    except Exception:
        pass


# Start the bot
bot.run(TOKEN)
