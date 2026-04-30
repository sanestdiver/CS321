import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"