import logging

import asyncpg.exceptions
import discord
from discord.ext import commands

import backend.command_checks
import backend.config
import backend.discord_events.on_reaction_add
import backend.day_themes

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
    await conn.execute(
        """INSERT INTO posted_inktober (message_id, user_id, message, inktober_day) VALUES($1, $2, $3, $4)""",
        int(message_id),
        int(user_id),
        message,
        "")


async def insert_day(message_id, day, conn):
    await conn.execute("""UPDATE posted_inktober SET inktober_day = $1 WHERE message_id = $2""", str(day), int(message_id))


async def fetch_day(message_id, conn):
    day = await conn.fetchval("""SELECT inktober_day FROM posted_inktober WHERE message_id = $1""", int(message_id))
    return day


async def insert_into_message_origin_tracking(message_id, my_message_id, channel_id, conn):
    log.info("Inserted {} | {} into tracker".format(message_id, my_message_id))
    await conn.execute(
        """INSERT INTO my_posts_to_original (original_id, my_message_id, my_channel_id) VALUES($1, $2, $3)""",
        int(message_id), int(my_message_id), int(channel_id))


async def check_if_in_tracking_table(message_id, conn):
    test = await conn.fetchval("""SELECT EXISTS (SELECT 1 from my_posts_to_original WHERE original_id = $1)""",
                               int(message_id))
    return test


async def grab_original_id(embed_id: int, conn):
    row = await conn.fetchrow("""SELECT original_id, my_channel_id FROM my_message_to_original WHERE my_message_id = $1""", int(embed_id))
    try:
        return row["original_id"], row["my_channel_id"]
    except TypeError as TE:
        log.warning("{} | {} | Can't find original id".format(TE, embed_id))


async def insert_original_id(embed_id, original_id, channel_id, conn):
    await conn.execute("""INSERT INTO my_message_to_original (my_message_id, original_id, my_channel_id) VALUES ($1, $2, $3)""", int(embed_id), int(original_id), int(channel_id))


async def fetch_from_tracking_table(message_id, conn):
    row = await conn.fetchrow(
        """SELECT my_message_id, my_channel_id FROM my_posts_to_original WHERE original_id = $1""",
        int(message_id))
    log.info("{}".format(row))
    return row["my_message_id"], row["my_channel_id"]


class Helper:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.check(backend.command_checks.is_authed)
    async def force_add_message(self, ctx: commands.Context):
        if len(ctx.message.content.split(" ")) != 3:
            await self.bot.say("I need a channel ID then a message ID in the format of "
                               "'command' channel_id message_id")
            return

        channel = ctx.message.content.split(" ")[1]
        message = ctx.message.content.split(" ")[2]

        fetched_channel = self.bot.get_channel(channel)
        if fetched_channel is None:
            await self.bot.say("Your first variable was a invalid channel ID")
            return

        try:
            fetched_message = await self.bot.get_message(fetched_channel, message)
        except discord.NotFound as DNF:
            await self.bot.say(DNF)
            return

        try:
            await backend.discord_events.on_reaction_add.new_inktober(fetched_message, self.bot)
            log.info("Forced added {} for {}".format(message, ctx.message.author.id))
            await self.bot.add_reaction(ctx.message, "\U00002705")
        except asyncpg.exceptions.UniqueViolationError as e:
            await self.bot.add_reaction(ctx.message, "\U0000274c")
            await self.bot.say(e)

    @commands.command(pass_context=True)
    @commands.check(backend.command_checks.is_authed)
    async def force_alter_day(self, ctx: commands.Context):
        if len(ctx.message.content.split(" ")) != 4:
            await self.bot.say("I need a channel ID then a message ID then a day (as a int) in the format of "
                               "'command' channel_id message_id day")
            return

        channel = ctx.message.content.split(" ")[1]
        message = ctx.message.content.split(" ")[2]
        try:
            day = int(ctx.message.content.split(" ")[3])
        except ValueError as VE:
            await self.bot.say(f"{VE} | on the day which should be your third variable")
            return

        fetched_channel = self.bot.get_channel(channel)
        if fetched_channel is None:
            await self.bot.say("Your first variable was a invalid channel ID")
            return

        try:
            fetched_message = await self.bot.get_message(fetched_channel, message)
        except discord.NotFound as DNF:
            await self.bot.say(DNF)
            return

        new_embed = fetched_message.embeds[0]
        log.info(new_embed)

        original_message_id, _ = await backend.helpers.grab_original_id(fetched_message.id, self.bot.db)
        await insert_day(original_message_id, day, self.bot.db)

        new_embed_embed = discord.Embed(timestamp=discord.utils.parse_time(new_embed["timestamp"]),
                                        title="Day {} ({})".format(str(day),
                                                                   backend.day_themes.day_themes[day]),
                                        colour=15169815)
        new_embed_embed.set_image(url=new_embed["image"]["url"])
        new_embed_embed.set_author(name=new_embed["author"]["name"],
                                   icon_url=new_embed["author"]["icon_url"])

        await self.bot.edit_message(fetched_message, embed=new_embed_embed)
        await self.bot.add_reaction(ctx.message, "\U00002705")

def setup(bot):
    bot.add_cog(Helper(bot))
