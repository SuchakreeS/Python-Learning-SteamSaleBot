import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


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


async def main():
    async with bot:
        await bot.load_extension("cogs.watchlist")
        await bot.load_extension("cogs.sales")
        await bot.load_extension("cogs.test_cog")
        await bot.start(token)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Bot shutting down...")