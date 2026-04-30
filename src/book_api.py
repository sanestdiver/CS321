# establishing imports
import aiohttp
from config import GOOGLE_API_KEY, GOOGLE_BOOKS_URL

# collecting from book_utils (part of business logic layer)
from book_utils import (
    clean_isbn,
    is_isbn,
    extract_isbn,
    generate_fake_price,
    get_numeric_price,
    build_goodreads_link,
    build_bookscouter_link,
)

# main persistance method (what app calls)
async def search_google_books(
    session: aiohttp.ClientSession,
    query: str,
    max_results: int = 5
) -> list[dict]:

    # query interpretation - handling some of the logic layer
    if is_isbn(query):
        search_query = f"isbn:{clean_isbn(query)}"
    else:
        search_query = f"intitle:{query}"
    
    # api request
    params = {
        "q": search_query,
        "maxResults": max_results,
        "printType": "books",
        "key": GOOGLE_API_KEY,
    }

    # core of request
    async with session.get(GOOGLE_BOOKS_URL, params=params) as response:
        # including error handling
        if response.status != 200:
            return []

        data = await response.json()

    items = data.get("items", [])
    books = []

    # parsing through result details
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

        retail_price = sale_info.get("retailPrice", {})
        amount = retail_price.get("amount")
        currency = retail_price.get("currencyCode")

        seed_value = isbn if isbn else title

        # pricing logic - extra handling
        if amount is not None and currency:
            display_price = f"{currency} {amount}"
            price_value = float(amount)
            price_is_estimated = False
        else:
            fake_price = generate_fake_price(seed_value)
            display_price = f"${fake_price} (estimated)"
            price_value = fake_price
            price_is_estimated = True

        # data transformation - putting into an actual result
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
            "price_is_estimated": price_is_estimated,
        })

    # sort results
    books.sort(key=get_numeric_price)
    return books