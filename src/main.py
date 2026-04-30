import discord
from discord.ext import commands
from config import TOKEN
from commands import setup_commands

intents = discord.Intents.default() #use discords default intents

bot = commands.Bot(command_prefix="!", intents=intents) #create bot instance

setup_commands(bot) #register slash commands

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync() #sync the slash commands so they show up in the server
        print(f"Logged in as {bot.user}")
        print(f"Synced {len(synced)} commands")

    except Exception as error:
        print(f"Sync failed: {error}") #print error if command sync fails

bot.run(TOKEN) #start bot