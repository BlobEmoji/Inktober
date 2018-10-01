import backend.config
import discord


async def user_role_authed(member: discord.Member):
    for role in member.roles:
        if role.id in backend.config.inktober_authed_roles:
            return True
    else:
        return False


class helper:
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(helper)
