from discord.ext import commands, tasks
import requests
import asyncio

from storage import load_watchlist, load_last_discounts, save_last_discounts


class SalesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.check_sales.start()

    @tasks.loop(seconds=60)
    async def check_sales(self):
        watchlist = load_watchlist()
        last_known_discounts = load_last_discounts()

        for appid, game_info in watchlist.items():
            watchers = game_info["watchers"]

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
                    user = await self.bot.fetch_user(watcher["user_id"])
                    await user.send(f"🔥 {name} is now {discount}% off!")

                    channel_id = watcher["channel_id"]
                    if channel_id not in notified_channels:
                        channel = self.bot.get_channel(channel_id)
                        await channel.send(f"🔥 {name} is now {discount}% off!")
                        notified_channels.add(channel_id)

            last_known_discounts[appid] = discount
            await asyncio.sleep(1)

        save_last_discounts(last_known_discounts)


async def setup(bot):
    await bot.add_cog(SalesCog(bot))