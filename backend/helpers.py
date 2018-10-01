import logging
import backend.config
import discord

log = logging.getLogger(__name__)


async def user_role_authed(member: discord.Member):
    for role in member.roles:
        if role.id in backend.config.inktober_authed_roles:
            return True
    else:
        return False


async def check_if_in_table(message_id, conn):
    test = await conn.fetchval("""SELECT EXISTS (SELECT 1 from posted_inktober WHERE message_id = $1)""",
                               int(message_id))
    return test


async def insert_into_table(message_id, user_id, conn):
    log.info("Inserted {} by {} into table".format(message_id, user_id))
    await conn.execute("""INSERT INTO posted_inktober (message_id, user_id) VALUES($1, $2)""", int(message_id),
                       int(user_id))


class Helper:
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Helper)
