import backend.config


async def is_authed(ctx):
    for role in ctx.message.author.roles:
        if role in backend.config.inktober_authed_roles:
            return True
    else:
        return False


class CommandChecks:
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(CommandChecks(bot))
