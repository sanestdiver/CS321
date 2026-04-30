import discord


# creates the main result embed
# formatting for title description price and links for the user
def create_result_embed(
    book: dict,
    query: str,
    index: int,
    is_cheapest: bool
) -> discord.Embed:

    # use isbn if available otherwise show n/a
    isbn_text = book["isbn"] if book["isbn"] else "N/A"

    # cut off description if too long
    short_description = book["description"]
    if len(short_description) > 220:
        short_description = short_description[:217] + "..."

    # add cheapest tag if this is the cheapest option
    title_prefix = "🏷️ Cheapest Option • " if is_cheapest else ""
    embed_title = f"{title_prefix}{index}. {book['title']}"

    # create embed with title description and color
    embed = discord.Embed(
        title=embed_title,
        description=short_description,
        #consider green or red
        color=discord.Color.gold() if is_cheapest else discord.Color.light_grey(),
    )

    # add standard book details - may change with more APIs
    embed.add_field(name="Search", value=query, inline=False)
    embed.add_field(name="Author(s)", value=book["authors"], inline=False)
    embed.add_field(name="Published", value=book["published"], inline=True)
    embed.add_field(name="ISBN", value=isbn_text, inline=True)
    embed.add_field(name="Pages", value=str(book["page_count"]), inline=True)
    embed.add_field(name="Category", value=book["categories"], inline=False)
    embed.add_field(name="💰 Price", value=book["price"], inline=False)

    # build list of external links
    links = []

    # include google books link if available
    if book["info_link"]:
        links.append(f"[Google Books]({book['info_link']})")

    # always include goodreads and bookscouter links
    links.append(f"[Goodreads]({book['goodreads']})")
    links.append(f"[BookScouter]({book['bookscouter']})")

    # add links field to embed
    embed.add_field(name="Links", value=" | ".join(links), inline=False)

    # set thumbnail
    if book["thumbnail"]:
        embed.set_thumbnail(url=book["thumbnail"])

    # set footer based on price type
    if is_cheapest:
        embed.set_footer(text="Lowest priced result shown for this search")
    elif book["price_is_estimated"]:
        embed.set_footer(text="Estimated demo price")
    else:
        embed.set_footer(text="Price from Google Books when available")

    return embed


# creates a placeholder embed
def create_placeholder_embed(title: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description="📦 Renting and combined listings are coming in a future update.",
        color=discord.Color.light_grey(),
    )


# help embed for help commands
def create_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📚 Book Finder Help",
        description="Search books by title or ISBN and view results sorted by cheapest price first.",
        color=discord.Color.blurple(),
    )

    # show example for title search
    embed.add_field(
        name="Search by title",
        value="`/buy query:Winnable`",
        inline=False,
    )

    # show example for isbn search
    embed.add_field(
        name="Search by ISBN",
        value="`/buy query:9780735211292`",
        inline=False,
    )

    # list placeholder commands
    embed.add_field(
        name="Placeholder commands",
        value="`/rent`\n`/all`",
        inline=False,
    )

    # describe what the user gets from a search
    embed.add_field(
        name="What you get",
        value=(
            "- Up to 5 results\n"
            "- Title searches ask you to confirm the edition\n"
            "- Cheapest result gets a badge\n"
            "- Real Google Books price if available\n"
            "- Estimated demo price otherwise\n"
            "- Google Books, Goodreads, and BookScouter links"
        ),
        inline=False,
    )

    # footer message
    embed.set_footer(text="Results are sorted cheapest first.")

    return embed