# establishing imports
import os
from dotenv import load_dotenv

# loading the environments
load_dotenv()

# actual api key establishing - for use
TOKEN = os.getenv("DISCORD_TOKEN") # keeping track of token access
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # standard api

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"