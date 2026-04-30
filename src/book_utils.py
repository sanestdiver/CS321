import re
import random
import urllib.parse

# Used to clean up the ISBN given by the user
def clean_isbn(query: str) -> str:
    return re.sub(r"[\s-]", "", query)

# Checks whether the current query matches the format of an ISBN
def is_isbn(query: str) -> bool:
    cleaned = clean_isbn(query)
    return bool(re.fullmatch(r"(\d{10}|\d{13})", cleaned))

# Returns the GoodReads link for the current book title
def build_goodreads_link(title: str) -> str:
    return f"https://www.goodreads.com/search?q={urllib.parse.quote(title)}"

# Returns the BookScouter link for the given book given a book Title OR an ISBN
def build_bookscouter_link(title: str, isbn: str | None) -> str:
    search_value = isbn if isbn else title # Uses the ISBN as the search term for the API if available, else it uses the given Title
    return f"https://bookscouter.com/search?query={urllib.parse.quote(search_value)}"

# Extracts the ISBN from the book data
def extract_isbn(volume_info: dict) -> str | None:
    identifiers = volume_info.get("industryIdentifiers", [])

    # For loops that look for the ISBN within the book data dict
    for ident in identifiers: # If the ISBN is 13 digits
        if ident.get("type") == "ISBN_13":
            return ident.get("identifier")

    for ident in identifiers: # If the ISBN is 10 digits
        if ident.get("type") == "ISBN_10":
            return ident.get("identifier")

    return None # Returns None if no ISBN was found

# Creates placeholder prices for each book listing
def generate_fake_price(seed_value: str) -> float:
    seeded_random = random.Random(seed_value)
    return round(seeded_random.uniform(25, 120), 2)

# Returns the price of the current book
def get_numeric_price(book: dict) -> float:
    return book["price_value"]