import asyncio
import logging
import random
from typing import TYPE_CHECKING
import typing
from discord import app_commands
import discord
from discord.ext import commands

from ballsdex.settings import settings
from ballsdex.core.models import BallInstance, Player
from ballsdex.packages.countryballs.countryball import CountryBall
from ballsdex.core.utils.transformers import BallTransform, SpecialTransform
from ballsdex.core.utils.logging import log_action

log = logging.getLogger("ballsdex.packages.owner.cog")

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

def check_for_owner():
    def predicate(ctx):
        return ctx.author.id in settings.co_owners
    return app_commands.check(predicate)

@commands.is_owner()
class Owner(commands.Cog):
    """
    Bot owners commands
    """

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot
        self.owner.parent = self.__cog_app_commands_group__
    owner = app_commands.Group(
        name=f"owner_{settings.collectible_name}s", description="Owner commands"
    )

    @owner.command(name="spawnball")
    @commands.is_owner()
    async def spawnball(
        self,
        interaction: discord.Interaction,
        countryball: BallTransform | None = None,
        channel: discord.TextChannel | None = None,
        n: int | None = None,
        visible: bool | None = None
    ):
        """
        Force spawn a random or specified countryball.

        Parameters:
        -----------
        countryball: Ball
            The countryball to spawn
        channel: discord.TextChannel
            The channel to spawn the ball in
        n: int
            The number of balls to spawn
        visible: bool
            Whether to send a message with the ball spawned
        """

        if (interaction.user.id not in settings.co_owners) and (interaction.user.id != 586539270014107671):
            await interaction.channel.send(f"Only co-owners can spawn balls, {interaction.user.mention}.")
            return

        if interaction.response.is_done():
            return
        await interaction.response.defer(ephemeral=True, thinking=True)

        randomized: bool

        if n is None:
            n = 1
        if visible is None:
            visible = True

        if not countryball:
            countryball = await CountryBall.get_random()
            randomized = True
        else:
            countryball = CountryBall(countryball)
            randomized = False

        i: int = 0
        while i < n:
            await countryball.spawn(channel or interaction.channel)  # type: ignore
            if randomized:
                countryball = await CountryBall.get_random()
            i += 1

        if n == 1:
            if countryball:
                if visible:
                    await interaction.followup.send(
                        f"{settings.collectible_name.title()} {countryball.name} spawned.",
                        ephemeral=False
                    )
                else:
                    await interaction.followup.send(
                        f"{settings.collectible_name.title()} {countryball.name} spawned, {interaction.user.mention}",
                        ephemeral=True
                    )
            else:
                if visible:
                    await interaction.followup.send(
                        f"{settings.collectible_name.title()} spawned.",
                        ephemeral=False
                    )
                else:
                    await interaction.followup.send(
                        f"{settings.collectible_name.title()} spawned, {interaction.user.mention}",
                    )
        else:
            if visible:
                await interaction.followup.send(
                    f"{n} balls spawned, {interaction.user.mention}.",
                        ephemeral=False
                )
            else:
                await interaction.followup.send(
                    f"{n} balls spawned, {interaction.user.mention}.",
                )

    @owner.command(name="giveball")
    @commands.is_owner()
    async def giveball(
        self,
        interaction: discord.Interaction,
        ball: BallTransform,
        user: discord.User,
        special: SpecialTransform | None = None,
        shiny: bool | None = None,
        health_bonus: int | None = None,
        attack_bonus: int | None = None,
        n: int | None = None,
        visible: bool | None = None,
    ):
        """
        Give the specified countryball to a player.

        Parameters
        ----------
        ball: Ball
        user: discord.User
        special: Special | None
        shiny: bool
            Omit this to make it random.
        health_bonus: int | None
            Omit this to make it random (-35/+40%).
        attack_bonus: int | None
            Omit this to make it random (-35/+40%).
        n: int | None
            The number of balls to give.
        visible: bool | None
            Whether the interaction user should be revealed.
        """

        if interaction.response.is_done():
            return
        await interaction.response.defer(ephemeral=True, thinking=True)

        if (interaction.user.id not in settings.co_owners) and (interaction.user.id != 586539270014107671):
            await interaction.channel.send(f"Only co-owners can spawn balls, {interaction.user.mention}.")
            return

        if n is None:
            n = 1
        if visible is None:
            visible = False

        player, created = await Player.get_or_create(discord_id=user.id)
        if n > 1:
            for i in range(n):
                instance = await BallInstance.create(
                    ball=ball,
                    player=player,
                    shiny=(shiny if shiny is not None else random.randint(1, 512) == 1),
                    attack_bonus=(attack_bonus if attack_bonus is not None else random.randint(-35, 40)),
                    health_bonus=(health_bonus if health_bonus is not None else random.randint(-35, 40)),
                    special=special,
                )
                await log_action(
                    f"{interaction.user} gave {settings.collectible_name} {ball.country} to {user}. "
                    f"Special={special.name if special else None} ATK={instance.attack_bonus:+d} "
                    f"HP={instance.health_bonus:+d} shiny={instance.shiny}",
                    self.bot,
                )
            if not visible:
                await interaction.followup.send(
                    f"`{ball.country}` {settings.collectible_name} were successfully given to `{user.mention}` by {interaction.user.mention} {n} times.\n"
                    f"Special: `{special.name if special else None}` • ATK:`{instance.attack_bonus:+d}` • "
                    f"HP:`{instance.health_bonus:+d}` • Shiny: `{instance.shiny}`",
                )
            else:
                await interaction.channel.send(
                    f"`{ball.country}` {settings.collectible_name} were successfully given to `{user.mention}` by {interaction.user.mention} {n} times.\n"
                    f"Special: `{special.name if special else None}` • ATK:`{instance.attack_bonus:+d}` • "
                    f"HP:`{instance.health_bonus:+d}` • Shiny: `{instance.shiny}`",
                )
        elif n == 1:
            instance = await BallInstance.create(
                ball=ball,
                player=player,
                shiny=(shiny if shiny is not None else random.randint(1, 512) == 1),
                attack_bonus=(attack_bonus if attack_bonus is not None else random.randint(-35, 40)),
                health_bonus=(health_bonus if health_bonus is not None else random.randint(-35, 40)),
                special=special,
            )
            if not visible:
                await interaction.followup.send(
                    f"`{ball.country}` {settings.collectible_name} was successfully given to `{user.mention}` by {interaction.user.mention}.\n"
                    f"Special: `{special.name if special else None}` • ATK:`{instance.attack_bonus:+d}` • "
                    f"HP:`{instance.health_bonus:+d}` • Shiny: `{instance.shiny}`",
                )
            else:
                await interaction.channel.send(
                    f"`{ball.country}` {settings.collectible_name} was successfully given to `{user.mention}` by {interaction.user.mention}.\n"
                    f"Special: `{special.name if special else None}` • ATK:`{instance.attack_bonus:+d}` • "
                    f"HP:`{instance.health_bonus:+d}` • Shiny: `{instance.shiny}`",
                )
            await log_action(
                f"{interaction.user} gave {settings.collectible_name} {ball.country} to {user}. "
                f"Special={special.name if special else None} ATK={instance.attack_bonus:+d} "
                f"HP={instance.health_bonus:+d} shiny={instance.shiny}",
                self.bot,
            )
        else:
            await interaction.followup.send(
                f"Amount must be a positive integer."
            )

    @owner.command(name="ping")
    @commands.is_owner()
    @app_commands.choices(language=[
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Hebrew", value="il"),
    ])
    @app_commands.choices(answer=[
        app_commands.Choice(name="Random", value="random"),
        app_commands.Choice(name="Oy gevalt", value="Oy gevalt"),
        app_commands.Choice(name="Oy vey", value="Oy vey"),
        app_commands.Choice(name="Ma laazazel", value="Ma laazazel"),
        app_commands.Choice(name="My owner is a Jew", value="My owner is a Jew"),
        app_commands.Choice(name="I feel like eating chleb", value="I feel like eating chleb"),
    ])
    async def ping(
        self,
        interaction: discord.Interaction,
        language: app_commands.Choice[str] | None = None,
        answer: app_commands.Choice[str] | None = None,
        ):
        """
        Makes the bot say random things.
        (Also usable by non-owners!)

        Parameters
        ----------
        language: str | None
            The language to use. Defaults to English.
        answer: str | None
            The message to send. Defaults to Random.
        """
        if (interaction.user.id not in settings.co_owners) and (interaction.user.id != 586539270014107671):
            await interaction.response.send_message(f"Wait your 30 seconds, {interaction.user.mention}.")
            await asyncio.sleep(30)
            return
        
        if language is None:
            language = app_commands.Choice(name="English", value="en")
        
        responses: list[str] = []

        def add_response(response: str, amount: int):
            for _ in range(amount):
                responses.append(response)

        if language.value == "en":
            if (answer is None) or (answer.name.lower() == "random"):

                add_response("Oy gevalt", 30)
                add_response("Oy vey", 20)
                add_response("Ma laazazel", 10)
                add_response("My owner is a Jew", 4)
                add_response("I feel like eating chleb", 2)
                add_response(f"{interaction.user.mention} is the winner!", 1)

                answer.name = random.choice(responses)

                await interaction.response.send_message(answer.name)
                return
            else:
                await interaction.response.send_message(answer.name)
                return
        elif language.value == "il":
            if (answer is None) or (answer.name.lower() == "random"):
                add_response("אוי געוואלד", 30)
                add_response("אוי ווי", 20)
                add_response("מה לעזאזל", 10)
                add_response("בעל הבוט הוא יהודי", 4)
                add_response("אני רעב", 2)
                add_response("הכל חוזר עליך וקקה בידך", 1)

                answer.name = random.choice(responses)
                await interaction.response.send_message(answer.name)
                return
            else:
                if answer.value == "Oy gevalt":
                    await interaction.response.send_message("אוי געוואלד")
                elif answer.value == "Oy vey":
                    await interaction.response.send_message("אוי ווי")
                elif answer.value == "Ma laazazel":
                    await interaction.response.send_message("מה לעזאזל")
                elif answer.value == "My owner is a Jew":
                    await interaction.response.send_message("בעל הבוט הוא יהודי")
                elif answer.value == "I feel like eating chleb":
                    await interaction.response.send_message("אני רעב")
                elif answer.value == "הכל חוזר עליך וקקה בידך":
                    await interaction.response.send_message("הכל חוזר עליך וקקה בידך")
                else:
                    await interaction.response.send_message(answer.value)
                return
        else:
            await interaction.response.send_message("Language not found.")
        