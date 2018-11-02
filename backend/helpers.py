import calendar
import datetime
import logging

import asyncpg.exceptions
import discord
from discord.ext import commands

import backend.command_checks
import backend.config
import backend.day_themes
import backend.discord_events.on_reaction_add
from bot import Bot as Client

log = logging.getLogger(__name__)


async def user_role_authed(member: discord.Member):
    for role in member.roles:
        if role.id in backend.config.inktober_authed_roles:
            return True
    else:
        return False


async def check_if_in_table(message_id: int, conn):
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
    log.info("{} {}".format(message_id, day))
    await conn.execute("""UPDATE posted_inktober SET inktober_day = $1 WHERE message_id = $2""", str(day),
                       int(message_id))


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
    row = await conn.fetchrow(
        """SELECT original_id, my_channel_id FROM my_message_to_original WHERE my_message_id = $1""", int(embed_id))
    try:
        return row["original_id"], row["my_channel_id"]
    except TypeError as TE:
        log.warning("{} | {} | Can't find original id".format(TE, embed_id))


async def insert_original_id(embed_id, original_id, channel_id, conn):
    await conn.execute(
        """INSERT INTO my_message_to_original (my_message_id, original_id, my_channel_id) VALUES ($1, $2, $3)""",
        int(embed_id), int(original_id), int(channel_id))


async def fetch_from_tracking_table(message_id, conn):
    row = await conn.fetchrow(
        """SELECT my_message_id, my_channel_id FROM my_posts_to_original WHERE original_id = $1""",
        int(message_id))
    log.info("{}".format(row))
    return row["my_message_id"], row["my_channel_id"]


async def count_author_submissions(user_id: int, conn):
    count = await conn.fetchval(
        """SELECT count(*) from posted_inktober where user_id = $1""", user_id)
    return count


async def fetch_days_of_submissions(user_id: int, conn):
    days = await conn.fetchval(
        """SELECT string_agg(inktober_day, '|') FROM posted_inktober WHERE user_id = $1""", user_id)
    return days


async def find_empty_days(conn):
    rows = await conn.fetch("""SELECT message_id, user_id from posted_inktober WHERE inktober_day = '' LIMIT 5""")
    new_rows = []
    row: asyncpg.Record
    for row in rows:
        new_rows.append({"message": row["message_id"],
                         "author": row["user_id"]})
    return new_rows


class DayInMonth(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        now: datetime.datetime = datetime.datetime.now()
        year: int = int(now.strftime("%Y"))
        month: int = int(now.strftime("%m"))
        month_data: tuple = calendar.monthrange(year, month)
        month_range: list = list(range(1, month_data[1] + 1))
        if int(argument) in month_range:
            return int(argument)
        else:
            raise commands.BadArgument("{} is not a valid day in the current month of {}".format(argument,
                                                                                                 now.strftime("%B")))


class Helper:
    def __init__(self, bot):
        self.bot: Client = bot

    @commands.command(pass_context=True,
                      aliases=["fadd"],
                      brief="Force add a message into the right channel")
    @commands.check(backend.command_checks.is_authed)
    async def force_add_message(self, ctx: commands.Context, channel: discord.TextChannel, message: int):
        log.info("{} {} {} {}".format(channel, message, type(channel), type(message)))
        try:
            fetched_message: discord.Message = await channel.get_message(message)
        except discord.NotFound as DNF:
            await ctx.send(DNF)
            return

        if fetched_message.author == self.bot.user:
            await ctx.send("Why are you trying to add a message from me?")
            return

        try:
            await backend.discord_events.on_reaction_add.new_inktober(fetched_message, self.bot)
            log.info("Forced added {} for {}".format(message, ctx.message.author.id))
            await ctx.message.add_reaction("\U00002705")
        except asyncpg.exceptions.UniqueViolationError as e:
            await ctx.message.add_reaction("\U0000274c")
            await ctx.send(e)

    @force_add_message.error
    async def force_add_message_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(error)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        else:
            log.warning("FAME")
            log.warning(type(error))
            log.warning(ctx)
            await ctx.send("{} {}".format(type(error), error))

    @commands.command(pass_context=True,
                      aliases=["fday"],
                      brief="Force alter the day of a already submitted piece")
    @commands.check(backend.command_checks.is_authed)
    async def force_alter_day(self, ctx: commands.Context, channel: discord.TextChannel, message: int, day: DayInMonth):
        log.info("{} {} {} {} {} {}".format(channel, message, day, type(channel), type(message), type(day)))
        try:
            fetched_message: discord.Message = await channel.get_message(message)
        except discord.NotFound as DNF:
            await ctx.send(DNF)
            return

        new_embed: discord.Embed = fetched_message.embeds[0]

        original_message_id, _ = await backend.helpers.grab_original_id(fetched_message.id, self.bot.db)
        await insert_day(original_message_id, day, self.bot.db)

        new_embed_embed = discord.Embed(timestamp=new_embed.timestamp,
                                        title="Day {} ({})".format(str(day),
                                                                   backend.day_themes.day_themes[day]),
                                        colour=15169815)
        new_embed_embed.set_image(url=new_embed.image.url)
        new_embed_embed.set_author(name=new_embed.author.name,
                                   icon_url=new_embed.author.icon_url)

        await fetched_message.edit(embed=new_embed_embed)
        await ctx.message.add_reaction("\U00002705")
        await fetched_message.add_reaction(backend.config.inktober_lock_image_button)

    @force_alter_day.error
    async def force_alter_day_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(error)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        else:
            log.info("TAE")
            log.info(type(error))
            log.info(ctx)
            await ctx.send("{} {}".format(type(error), error))

    @commands.command(pass_context=True,
                      aliases=["foriginal"],
                      brief="Allows you to find the posted inktober from the original message id")
    @commands.check(backend.command_checks.is_authed)
    async def find_original(self, ctx: commands.Context, channel: discord.TextChannel, message: int):
        try:
            fetched_message: discord.Message = await channel.get_message(message)
        except discord.NotFound as DNF:
            await ctx.send(DNF)
            return

        try:
            my_message_id, my_channel_id = await fetch_from_tracking_table(message, self.bot.db)
        except TypeError as TE:
            log.warning("find_original | {} | {} {}".format(TE, channel.id, message))
            await ctx.send("That message from that channel was not found in the DB")
        else:
            await ctx.send("https://discordapp.com/channels/{}/{}/{}".format(ctx.guild.id,
                                                                             my_channel_id,
                                                                             my_message_id))

    @find_original.error
    async def find_original_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(error)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        else:
            log.info("FOE")
            log.info(type(error))
            log.info(ctx)
            await ctx.send("{} {}".format(type(error), error))

    @commands.command(pass_context=True,
                      brief="Given a user find the amount of posts + what day")
    @commands.check(backend.command_checks.is_authed)
    async def inktober_info(self, ctx: commands.Context, user: discord.Member):
        submission_amount = await count_author_submissions(user.id, self.bot.db)
        days = await fetch_days_of_submissions(user.id, self.bot.db)

        embed = discord.Embed(colour=15169815)
        embed.add_field(name="Amount", value=submission_amount)
        embed.add_field(name="Days", value=", ".join(str(day) for day in days.split("|")))
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(pass_context=True,
                      brief="Finds empty days and links message")
    @commands.check(backend.command_checks.is_authed)
    async def find_blank(self, ctx: commands.Context):
        blank_ids = await find_empty_days(self.bot.db)
        if len(blank_ids) == 0:
            await ctx.send("None found that are empty")
            return

        messages_to_fix = []
        for message_id in blank_ids:
            my_message_id, my_channel_id = await fetch_from_tracking_table(message_id["message"], self.bot.db)
            messages_to_fix.append({"link": f"https://discordapp.com/channels/{ctx.guild.id}/{my_channel_id}/{my_message_id}",
                                    "channel": my_channel_id,
                                    "message": my_message_id,
                                    "author": message_id["author"]})

        embed = discord.Embed()
        for message in messages_to_fix:
            embed.add_field(name=f"<@!{message['author']}>", value=message["link"])

        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    # @commands.check(backend.command_checks.is_authed)
    @commands.is_owner()
    async def _old_force_add_message(self, ctx: commands.Context):
        """
        Forces adds a message into the inktober channel
        if you specify the channel_id message_id
        """
        if len(ctx.message.content.split(" ")) != 3:
            await ctx.send("I need a channel ID then a message ID in the format of "
                           "'command' channel_id message_id")
            return

        channel = ctx.message.content.split(" ")[1]
        message = ctx.message.content.split(" ")[2]

        fetched_channel = self.bot.get_channel(channel)
        if fetched_channel is None:
            await ctx.send("Your first variable was a invalid channel ID")
            return

        try:
            fetched_message = await fetched_channel.get_message(fetched_channel, message)
        except discord.NotFound as DNF:
            await ctx.send(DNF)
            return

        try:
            await backend.discord_events.on_reaction_add.new_inktober(fetched_message, self.bot)
            log.info("Forced added {} for {}".format(message, ctx.message.author.id))
            await ctx.message.add_reaction("\U00002705")
        except asyncpg.exceptions.UniqueViolationError as e:
            await ctx.message.add_reaction("\U0000274c")
            await ctx.message.send(e)

    @commands.command(pass_context=True)
    # @commands.check(backend.command_checks.is_authed)
    @commands.is_owner()
    async def _old_force_alter_day(self, ctx: commands.Context):
        """
        Force alters the set day for a already sent inktober post
        if you give it the channel_id message_id date
        """
        if len(ctx.message.content.split(" ")) != 4:
            await ctx.send("I need a channel ID then a message ID then a day (as a int) in the format of "
                           "'command' channel_id message_id day")
            return

        channel = ctx.message.content.split(" ")[1]
        message = ctx.message.content.split(" ")[2]
        try:
            day = int(ctx.message.content.split(" ")[3])
        except ValueError as VE:
            await ctx.send(f"{VE} | on the day which should be your third variable")
            return

        fetched_channel: discord.TextChannel = ctx.guild.get_channel(int(channel))
        if fetched_channel is None:
            await ctx.send("Your first variable was a invalid channel ID")
            return

        try:
            fetched_message: discord.Message = await fetched_channel.get_message(int(message))
        except discord.NotFound as DNF:
            await ctx.send(DNF)
            return

        new_embed: discord.Embed = fetched_message.embeds[0]
        log.info(new_embed)

        original_message_id, _ = await backend.helpers.grab_original_id(fetched_message.id, self.bot.db)
        await insert_day(original_message_id, day, self.bot.db)

        new_embed_embed = discord.Embed(timestamp=new_embed.timestamp,
                                        title="Day {} ({})".format(str(day),
                                                                   backend.day_themes.day_themes[day]),
                                        colour=15169815)
        new_embed_embed.set_image(url=new_embed.image.url)
        new_embed_embed.set_author(name=new_embed.author.name,
                                   icon_url=new_embed.author.icon_url)

        await fetched_message.edit(embed=new_embed_embed)
        await ctx.message.add_reaction("\U00002705")
        await fetched_message.add_reaction(backend.config.inktober_lock_image_button)


def setup(bot):
    bot.add_cog(Helper(bot))
