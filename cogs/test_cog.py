from discord.ext import commands
from discord import app_commands
import discord

class Watchlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong")

    @app_commands.command(name="ping", description="Check to see if bot is working")
    async def slash_ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

async def setup(bot):
    await bot.add_cog(Watchlist(bot))