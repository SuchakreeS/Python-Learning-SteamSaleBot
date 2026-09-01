from discord.ext import commands
import requests

from storage import load_watchlist, save_watchlist, extract_appid


class WatchlistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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


async def setup(bot):
    await bot.add_cog(WatchlistCog(bot))