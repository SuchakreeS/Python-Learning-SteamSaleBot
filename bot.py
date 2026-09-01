import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import json
import requests
import asyncio

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
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f, indent=2)


def load_last_discounts():
    try:
        with open(LAST_DISCOUNTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_last_discounts(discounts):
    with open(LAST_DISCOUNTS_FILE, "w") as f:
        json.dump(discounts, f, indent=2)


# ↓↓↓ NEW ↓↓↓
def extract_appid(text):
    if text.isdigit():
        return text

    parts = text.split("/")
    if "app" in parts:
        app_index = parts.index("app")
        return parts[app_index + 1]

    return None
# ↑↑↑ NEW ↑↑↑


@tasks.loop(seconds=60)
async def check_sales():
    watchlist = load_watchlist()
    last_known_discounts = load_last_discounts()

    # ↓↓↓ CHANGED — reads new nested shape ↓↓↓
    for appid, game_info in watchlist.items():
        watchers = game_info["watchers"]
    # ↑↑↑ CHANGED ↑↑↑

        try:
            details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            details_res = requests.get(details_url)
            details_data = details_res.json()

            game_data = details_data[appid]["data"]
            name = game_data["name"]
            price_overview = game_data.get("price_overview", {})
            discount = price_overview.get("discount_percent", 0)
        except Exception as e:
            print(f"Failed to check app id {appid}, {e}")
            continue

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
        await asyncio.sleep(1)

    save_last_discounts(last_known_discounts)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_sales.start()


@bot.event
async def on_message(message):
    print(f"Received: {message.content} from {message.author}")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument! Usage: `!{ctx.command} <link or appid>`")
    else:
        print(f"Unhandled error in command {ctx.command}: {error}")
        await ctx.send("Something went wrong running that command.")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


# ↓↓↓ CHANGED — new shape, fetches + stores name ↓↓↓
@bot.command()
async def watch(ctx, *, game):
    appid = extract_appid(game)
    if appid is None:
        await ctx.send("That doesn't look like a valid Steam link or appid!!!")
        return

    watchlist = load_watchlist()

    if appid not in watchlist:
        try:
            details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            details_res = requests.get(details_url)
            details_data = details_res.json()
            name = details_data[appid]["data"]["name"]
        except Exception:
            name = "Unknown Game"

        watchlist[appid] = {"name": name, "watchers": []}

    already_watching = any(
        w["user_id"] == ctx.author.id for w in watchlist[appid]["watchers"]
    )

    if not already_watching:
        watchlist[appid]["watchers"].append(
            {"user_id": ctx.author.id, "channel_id": ctx.channel.id}
        )

    save_watchlist(watchlist)

    await ctx.send(f"Got it! Watching {watchlist[appid]['name']} (appid: {appid})")
# ↑↑↑ CHANGED ↑↑↑


@bot.command()
async def unwatch(ctx, *, game):
    watchlist = load_watchlist()
    appid = extract_appid(game)

    if appid is None:
        matches = [
            aid for aid, info in watchlist.items()
            if game.lower() in info['name'].lower()
        ]

        if len(matches) == 0:
            await ctx.send("Couldn't find a game matching that name")
            return
        elif len(matches) > 1:
            names = ", ".join(watchlist[aid]["name"] for aid in matches)
            await ctx.send(f"Multiple matches found: {names} try a more specific name")
            return

        appid = matches[0]

    if appid not in watchlist:
        await ctx.send("You're not watching that game")
        return

    name = watchlist[appid]["name"]

    watchlist[appid]["watchers"] = [
        w for w in watchlist[appid]["watchers"] if w["user_id"] != ctx.author.id
    ]

    if not watchlist[appid]["watchers"]:
        del watchlist[appid]

    save_watchlist(watchlist)

    await ctx.send(f"Stopped watching {name}")

@bot.command()
async def mylist(ctx):
    watchlist = load_watchlist()

    watching = [
        info["name"] for info in watchlist.values()
        if any(w["user_id"] == ctx.author.id for w in info["watchers"])
    ]

    if not watching:
        await ctx.send("You're not watching any games yet!")
        return

    games_list = "\n".join(f"• {name}" for name in watching)
    await ctx.send(f"You're watching: \n{games_list}")

bot.run(token)  # Must always be at the bottom