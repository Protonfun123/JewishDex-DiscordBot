import logging
import random
import time
from typing import TYPE_CHECKING

import discord

from discord.ext import commands
from ballsdex import settings
from ballsdex.core.models import Ball, BallInstance, Player, Special
from ballsdex.packages.countryballs.components import CountryballNamePrompt
from ballsdex.packages.countryballs.countryball import CountryBall
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist
from ballsdex.settings import settings

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
        await ctx.send("Oy gevalt")

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
        Force spawn a Jewishball.
        """
        if not ball:
            countryball = await CountryBall.get_random()
        else:
            try:
                ball_model = await Ball.get(country__iexact=ball.lower())
            except DoesNotExist:
                await ctx.send(f"No such {settings.collictible_name.title()} exists.")
                return
            countryball = CountryBall(ball_model)
        countryball.message = f"{ctx.author.mention} spawned a {settings.collectible_name}!"

        await countryball.spawn(channel or ctx.channel)
        await ctx.message.add_reaction("✅")

    @commands.command()
    @commands.is_owner()
    async def giveball(
        self,
        ctx: commands.Context,
        ball: str,
        *users: discord.User
    ):
        """
        Give a Jewishball to one or more users.

        If the Jewishball name has spaces, put it between quotes.
        Multiple users may be given to afterwards (mention or ID).
        """
        if not users:
            ctx.send(f"User not specified. Giving {settings.collectible_name.title()} to {ctx.author.mention}.")
            users[0] = ctx.author
        try:
            ball_model = await Ball.get(country__iexact=ball.lower())
        except DoesNotExist:
            await ctx.send(f"No such {settings.collictible_name.title()} exists. Picking random.")
            ball_model = await Ball.get_random()

        # Really ugly.
        fake_prompt = CountryballNamePrompt(CountryBall(ball_model), None)
        async with ctx.typing():
            for user in users:
                await fake_prompt.catch_ball(ctx.bot, user)
        if len(users) > 1:
            await ctx.send(f"{settings.collectible_name.title()} {ball_model.country} given to {len(users)} users.")
        else:
            await ctx.send(f"{settings.collectible_name.title()} {ball_model.country} was given to {users[0].mention}.")

    @commands.command()
    @commands.is_owner()
    async def special_give(
        self,
        ctx: commands.Context,
        user: discord.User.id,
        ball: str,
        shiny: bool,
        ab: int,
        hb: int,
        special: str | None = None,
    ):
        """
        Give a Jewishball to a user, with a specified special, shiny, attack bonus, and health bonus.
        Seperate parameters with a comma: ,
        Paramters:
        user: discord.User.id
        ball: str
        special: str | None
        shiny: bool
        ab: int
        hb: int
        """

        if not user:
            user = ctx.message.author

        if not ball or not special or not ab or not hb:
            await ctx.send("Please provide all required arguments.")
            return
        
        if ball.lower().startswith("\"") and ball.lower().endswith("\""):
            ball = ball[1:-1]

        player, created = await Player.get_or_create(discord_id=user.id)
        special_obj = await Special.get(name__iexact=special.lower())
        ball_obj = await Ball.filter(country__iexact=ball.lower()).first()

        if not ball_obj:
            await ctx.send("No such ball exists.")
            return

        await BallInstance.create(
            ball=ball_obj,
            player=player,
            shiny=(bool(shiny) if shiny is not None else random.randint(1, 512) == 1),
            attack_bonus=ab,
            health_bonus=hb,
            special=special_obj,
        )

        await ctx.send(f"Special give successful!")
    