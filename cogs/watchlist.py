from discord.ext import commands
import requests
from discord import app_commands
import discord

from storage import load_watchlist, save_watchlist, extract_appid


class WatchlistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
# "!" Command
    @commands.command()
    async def watch(self, ctx, *, game):
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

    @commands.command()
    async def unwatch(self, ctx, *, game):
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

    @commands.command()
    async def mylist(self, ctx):
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

# / Command
    @app_commands.command(name="watch", description="Watch a Steam game for sales")
    @app_commands.describe(game="A Steam link, appid, or game name")
    async def slash_watch(self, interaction: discord.Interaction, game: str):
        appid = extract_appid(game)
        if appid is None:
            await interaction.response.send_message("That doesn't look like a valid Steam link or appid!!!")
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
            w["user_id"] == interaction.user.id for w in watchlist[appid]["watchers"]
        )

        if not already_watching:
            watchlist[appid]["watchers"].append(
                {"user_id": interaction.user.id, "channel_id": interaction.channel_id}
            )

        save_watchlist(watchlist)

        await interaction.response.send_message(
            f"Got it! Watching {watchlist[appid]['name']} (appid: {appid})"
        )

    @app_commands.command(name="mylist", description="See everything you're watching")
    async def slash_mylist(self, interaction: discord.Interaction):
        watchlist = load_watchlist()

        watching = [
            info["name"] for info in watchlist.values()
            if any(w["user_id"] == interaction.user.id for w in info["watchers"])
        ]

        if not watching:
            await interaction.response.send_message("You're not watching any games yet!")
            return

        games_list = "\n".join(f"• {name}" for name in watching)
        await interaction.response.send_message(f"You're watching:\n{games_list}")

    async def unwatch_autocomplete(self, interaction: discord.Interaction, current: str):
        watchlist = load_watchlist()

        matches = [
            info["name"] for info in watchlist.values()
            if current.lower() in info["name"].lower()
            and any(w["user_id"] == interaction.user.id for w in info["watchers"])
        ]

        return [
            app_commands.Choice(name=name, value=name)
            for name in matches[:25]
        ]
    @app_commands.command(name="unwatch", description="Remove the game from my list")
    @app_commands.describe(game="Which game to remove?")
    @app_commands.autocomplete(game=unwatch_autocomplete)
    async def slash_unwatch(self, interaction: discord.Interaction, game:str):
        watchlist = load_watchlist()
        appid = extract_appid(game)

        if appid is None:
            matches = [
                aid for aid, info in watchlist.items()
                if game.lower() in info['name'].lower()
            ]
            if len(matches) == 0:
                await interaction.response.send_message("Couldn't find a game matching that name")
                return
            elif len(matches) > 1:
                names = ", ".join(watchlist[aid]["name"] for aid in matches)
                await interaction.response.send_message(f"Multiple matches found: {names} try a more specific name")
                return

            appid = matches[0]

        if appid not in watchlist:
            await interaction.response.send_message("You're not watching that game")
            return

        name = watchlist[appid]["name"]

        watchlist[appid]["watchers"] = [
            w for w in watchlist[appid]["watchers"] if w["user_id"] != interaction.user.id
        ]

        if not watchlist[appid]["watchers"]:
            del watchlist[appid]

        save_watchlist(watchlist)

        await interaction.response.send_message(f"Stopped watching {name}")


async def setup(bot):
    await bot.add_cog(WatchlistCog(bot))