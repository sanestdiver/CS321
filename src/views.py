import aiohttp
import discord
from discord.ui import View, Select

from book_api import search_google_books #import Google Books API

from embeds import create_result_embed #import whats needed to embed messages in Discord


#creates the dropdown menu that lets the user choose a book edition
class BookSelect(Select):
    def __init__(
        self,
        books: list[dict],
        original_user: discord.User | discord.Member,
        original_query: str
    ):
        self.books = books #store books returned from search
        self.original_user = original_user #store user that searched
        self.original_query = original_query #store original search query for result embeds
        options = []
        for index, book in enumerate(books): #loop through each book to create embed
            title_text = book["title"][:100] #Discord limits to 100 characters
            author_and_isbn = f"{book['authors']} • {book['isbn'] if book['isbn'] else 'No ISBN'}" #create dropdown description or no ISBN
            #add the book as an option in the dropdown
            options.append(
                discord.SelectOption(
                    label=title_text,
                    description=author_and_isbn[:100],
                    value=str(index),
                )
            )

        #initialize the select dropdown
        super().__init__(
            placeholder="Confirm Book edition",
            min_values=1,
            max_values=1,
            options=options,
        )

    #runs when the user selects a book from the dropdown
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.original_user.id: #check if person using is the same person who started the search
            await interaction.response.send_message( #only if no book is foung
                "Only the user who started this search can confirm the book.",
                ephemeral=True,
            )
            return

        selected_index = int(self.values[0]) #get dropdown and convert it to an index
        selected_book = self.books[selected_index] #use index to find the book
        self.disabled = True #disable dropdown after selection
        await interaction.response.edit_message(view=self.view) #show disabled dropdown
        await interaction.followup.send( #confirm selected book
            f"✅ Selected: **{selected_book['title']}**",
            ephemeral=False,
        )
        if selected_book["isbn"]: #if book has ISBN search again using it
            async with aiohttp.ClientSession() as session:
                confirmed_books = await search_google_books(
                    session,
                    selected_book["isbn"],
                    max_results=5,
                )
        else:
            confirmed_books = [selected_book] #no ISBN keep original selection
        if not confirmed_books: #if no ISBN keep original selection
            confirmed_books = [selected_book]
        
        embeds = []
        for index, book_item in enumerate(confirmed_books, start=1):
            is_cheapest = index == 1 #cheapest result
            embeds.append( #create embed for cheapest result
                create_result_embed(
                    book_item,
                    self.original_query,
                    index,
                    is_cheapest,
                )
            )
        await interaction.followup.send(embeds=embeds) #send final book as embeds


#creates the Discord view that holds the book selection dropdown
class BookSelectView(View):
    def __init__(
        self,
        books: list[dict],
        original_user: discord.User | discord.Member,
        original_query: str
    ):
        super().__init__(timeout=None) #initialize the view with no timeout so it doesnt automatically expire
        self.add_item(BookSelect(books, original_user, original_query)) #add the BookSelect dropdown to this view