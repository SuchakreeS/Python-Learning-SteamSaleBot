import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import json
import requests

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

WATCHLIST_FILE = "watchlist.json"
LAST_DISCOUNTS_FILE = "last_discounts.json"

def load_watchlist():
    try:
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(watchlist, f, indent=2)

def load_last_discounts() :
    try :
        with open(LAST_DISCOUNTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_last_discounts(discounts):
    with open(LAST_DISCOUNTS_FILE, 'w') as f:
        json.dump(discounts, f, indent=2)


@tasks.loop(seconds=60)
async def check_sales():
    watchlist = load_watchlist()
    last_known_discounts = load_last_discounts()

    for appid, watchers in watchlist.items():
        details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        details_res = requests.get(details_url)
        details_data = details_res.json()

        game_data = details_data[appid]["data"]
        name = game_data["name"]
        price_overview = game_data.get("price_overview", {})
        discount = price_overview.get("discount_percent", 0)

        last_discount = last_known_discounts.get(appid, 0)

        if discount > 0 and discount != last_discount:
            notified_channels = set()

            for watcher in watchers:
                user = await bot.fetch_user(watcher["user_id"])
                await user.send(f"🔥 {name} is now {discount}% off!")

                channel_id = watcher["channel_id"]
                if channel_id not in notified_channels:
                    channel = bot.get_channel(channel_id)
                    await channel.send(f"🔥 {name} is now {discount}% off!")
                    notified_channels.add(channel_id)

        last_known_discounts[appid] = discount
    save_last_discounts(last_known_discounts)


@bot.event
async def on_ready() :
    print(f"Logged in as {bot.user}")
    check_sales.start()

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

    already_watching = any(w["user_id"] == ctx.author.id for w in watchlist[appid])

    if not already_watching:
        watchlist[appid].append({
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id
        })

    save_watchlist(watchlist)

    await ctx.send(f"Got it! watching for {appid}")


bot.run(token) #Must always be at the bottom