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


async def insert_into_table(message_id, user_id, message, conn):
    log.info("Inserted {} by {} into table".format(message_id, user_id))
    await conn.execute("""INSERT INTO posted_inktober (message_id, user_id, message) VALUES($1, $2, $3)""", int(message_id),
                       int(user_id), message)


async def insert_into_message_origin_tracking(message_id, my_message_id, channel_id, conn):
    log.info("Inserted {} | {} into tracker".format(message_id, my_message_id))
    await conn.execute("""INSERT INTO my_posts_to_original (original_id, my_message_id, my_channel_id) VALUES($1, $2, $3)""", int(message_id), int(my_message_id), int(channel_id))


async def check_if_in_tracking_table(message_id, conn):
    test = await conn.fetchval("""SELECT EXISTS (SELECT 1 from my_posts_to_original WHERE message_id = $1)""",
                               int(message_id))
    return test


async def fetch_from_tracking_table(message_id, conn):
    my_message_id, channel_id = await conn.fetchval("""SELECT my_message_id, my_channel_id FROM my_posts_to_original WHERE message_id = $1""",
                               int(message_id))
    return my_message_id, channel_id


class Helper:
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Helper)
