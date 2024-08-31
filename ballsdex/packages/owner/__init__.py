import logging

from ballsdex.core.bot import BallsDexBot
from ballsdex.packages.owner.cog import Owner

from discord import app_commands

log = logging.getLogger("ballsdex.packages.owner")

def command_count(cog: Owner) -> int:
    total = 0
    for command in cog.walk_app_commands():
        total += len(command.name) + len(command.description)
        if isinstance(command, app_commands.Group):
            continue
        for param in command.parameters:
            total += len(param.name) + len(param.description)
            for choice in param.choices:
                total += len(choice.name) + (
                    int(choice.value)
                    if isinstance(choice.value, int | float)
                    else len(choice.value)
                )
    return total

def strip_descriptions(cog: Owner):
    for command in cog.walk_app_commands():
        command.description = "."
        if isinstance(command, app_commands.Group):
            continue
        for param in command.parameters:
            param._Parameter__parent.description = "."  # type: ignore

async def setup(bot: "BallsDexBot"):
    n = Owner(bot)
    if command_count(n) > 3900:
        strip_descriptions(n)
        log.warn("/owner command too long, stripping descriptions")
    await bot.add_cog(n)
