import logging
import random
import time
from typing import TYPE_CHECKING

import discord

from discord.ext import commands
from ballsdex.core.models import Ball, BallInstance, Player
from ballsdex.packages.countryballs.countryball import CountryBall
from tortoise import Tortoise
from ballsdex.core.utils.transformers import BallTransform
from tortoise.exceptions import DoesNotExist

log = logging.getLogger("ballsdex.core.commands")

if TYPE_CHECKING:
    from .bot import BallsDexBot


class Core(commands.Cog):
    """
    Core commands of BallsDex bot
    """

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Ping!
        """
        await ctx.send("Pong")

    @commands.command()
    @commands.is_owner()
    async def reloadtree(self, ctx: commands.Context):
        """
        Sync the application commands with Discord
        """
        await self.bot.tree.sync()
        await ctx.send("Application commands tree reloaded.")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, package: str):
        """
        Reload an extension
        """
        package = "ballsdex.packages." + package
        try:
            try:
                await self.bot.reload_extension(package)
            except commands.ExtensionNotLoaded:
                await self.bot.load_extension(package)
        except commands.ExtensionNotFound:
            await ctx.send("Extension not found")
        except Exception:
            await ctx.send("Failed to reload extension.")
            log.error(f"Failed to reload extension {package}", exc_info=True)
        else:
            await ctx.send("Extension reloaded.")

    @commands.command()
    @commands.is_owner()
    async def reloadcache(self, ctx: commands.Context):
        """
        Reload the cache of database models.

        This is needed each time the database is updated, otherwise changes won't reflect until
        next start.
        """
        await self.bot.load_cache()
        await ctx.message.add_reaction("✅")

    @commands.command()
    @commands.is_owner()
    async def analyzedb(self, ctx: commands.Context):
        """
        Analyze the database. This refreshes the counts displayed by the `/about` command.
        """
        connection = Tortoise.get_connection("default")
        t1 = time.time()
        await connection.execute_query("ANALYZE")
        t2 = time.time()
        await ctx.send(f"Analyzed database in {round((t2 - t1) * 1000)}ms.")

    @commands.command()
    @commands.is_owner()
    async def spawnball(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        *,
        ball: str | None = None,
    ):
        """
        Force spawn a countryball.
        """
        if not ball:
            countryball = await CountryBall.get_random()
        else:
            try:
                ball_model = await Ball.get(country__iexact=ball.lower())
            except DoesNotExist:
                await ctx.send("No such countryball exists.")
                return
            countryball = CountryBall(ball_model)
        await countryball.spawn(channel or ctx.channel)
        await ctx.message.add_reaction("✅")
