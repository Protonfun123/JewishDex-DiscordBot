import logging
import random
import string
from datetime import datetime

import discord

from ballsdex.core.models import Ball, balls
from ballsdex.packages.countryballs.components import CatchView
from ballsdex.settings import settings

log = logging.getLogger("ballsdex.packages.countryballs")


class CountryBall:
    def __init__(self, model: Ball):
        self.name = model.country
        self.model = model
        self.message: discord.Message = discord.utils.MISSING
        self.catched = False
        self.time = datetime.now()

    @classmethod
    async def get_random(cls):
        countryballs = list(filter(lambda m: m.enabled, balls.values()))
        if not countryballs:
            raise RuntimeError("No ball to spawn")
        rarities = [x.rarity for x in countryballs]
        cb = random.choices(population=countryballs, weights=rarities, k=1)[0]
        return cls(cb)

    async def spawn(self, channel: discord.TextChannel) -> bool:
        """
        Spawn a countryball in a channel.

        Parameters
        ----------
        channel: discord.TextChannel
            The channel where to spawn the countryball. Must have permission to send messages
            and upload files as a bot (not through interactions).

        Returns
        -------
        bool
            `True` if the operation succeeded, otherwise `False`. An error will be displayed
            in the logs if that's the case.
        """

        def generate_random_name():
            source = string.ascii_uppercase + string.ascii_lowercase + string.ascii_letters
            return "".join(random.choices(source, k=15))
        
        def generate_spawn_message() -> str:
            possibilities: list[str] = [
                f"A wild {settings.collectible_name.title()} appeared! Mazal tov!",
                f"A wild {settings.collectible_name.title()} appeared! Mazal tov!",
                f"A wild {settings.collectible_name.title()} appeared! Mazal tov!",
                f"A wild {settings.collectible_name.title()} appeared! Mazal tov!",
                f"A wild {settings.collectible_name.title()} appeared! Mazal tov!",
                f"No way! This is a wild {settings.collectible_name.title()}!",
                f"No way! This is a wild {settings.collectible_name.title()}!",
                f"No way! This is a wild {settings.collectible_name.title()}!",
                f"No way! This is a wild {settings.collectible_name.title()}!",
                f"No way! This is a wild {settings.collectible_name.title()}!",
                f"No way! The bot owner is Jewish!"
            ]
            num: int = random.randint(0, len(possibilities) - 1)
            return possibilities[num]

        extension = self.model.wild_card.split(".")[-1]
        file_location = "." + self.model.wild_card
        file_name = f"nt_{generate_random_name()}.{extension}"
        try:
            permissions = channel.permissions_for(channel.guild.me)
            if permissions.attach_files and permissions.send_messages:
                self.message = await channel.send(
                    generate_spawn_message(),
                    view=CatchView(self),
                    file=discord.File(file_location, filename=file_name),
                )
                return True
            else:
                log.error("Missing permission to spawn ball in channel %s.", channel)
        except discord.Forbidden:
            log.error(f"Missing permission to spawn ball in channel {channel}.")
        except discord.HTTPException:
            log.error("Failed to spawn ball", exc_info=True)
        return False
