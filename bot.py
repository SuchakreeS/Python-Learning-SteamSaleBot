import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import json

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    try:
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(watchlist, f, indent=2)

@tasks.loop(seconds=60)
async def test_loop() :
    print("Checking...")

@bot.event
async def on_ready() :
    print(f"Logged in as {bot.user}")
    test_loop.start()

@bot.event
async def on_message(message):
    print(f"Received: {message.content} from {message.author}")
    await bot.process_commands(message)

@bot.command()
async def ping(ctx) :
    await ctx.send("Pong!")


@bot.command()
async def watch(ctx, link) :
    try:
        parts = link.split("/")
        app_index = parts.index("app")
        appid = parts[app_index + 1]
    except ValueError:
        await ctx.send("That doesn't look like valid steam link!!!")
        return

    watchlist = load_watchlist()

    if appid not in watchlist:
        watchlist[appid] = []

    if ctx.author.id not in watchlist[appid] :
        watchlist[appid].append(ctx.author.id)

    save_watchlist(watchlist)

    await ctx.send(f"Got it! watching for {appid}")


bot.run(token) #Must always be at the bottom