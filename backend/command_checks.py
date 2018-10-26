import backend.config
from bot import Bot as Client
from discord.ext import commands


async def is_authed(ctx: commands.Context):
    for role in ctx.message.author.roles:
        if role.id in backend.config.inktober_authed_roles:
            return True
    else:
        return False


class CommandChecks:
    def __init__(self, bot):
        self.bot: Client = bot


def setup(bot):
    bot.add_cog(CommandChecks(bot))
