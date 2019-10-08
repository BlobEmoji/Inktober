import calendar
import datetime
import logging
from typing import Union

import discord
import discord.errors
from discord.ext import commands

import backend.config
import backend.day_themes
import backend.helpers
import backend.sheets.sheets
from bot import Bot as Client

log = logging.getLogger(__name__)


async def inktober_post(message: discord.Message, bot_spam: discord.TextChannel):
    embed: discord.Embed = discord.Embed(timestamp=message.created_at, colour=15169815)
    message.attachments[0]: discord.Attachment

    embed.set_image(url=message.attachments[0].proxy_url)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    my_id = await bot_spam.send(embed=embed)

    for emote in backend.config.date_buttons:
        await my_id.add_reaction(emote)

    return my_id


async def location_check(message: discord.Message):
    if message.guild.id == backend.config.inktober_server:
        if message.channel.id in backend.config.inktober_authed_channels:
            log.info("Inktober authed")
            return True
    return False


async def new_inktober(message: discord.Message, bot: Client):
    await backend.helpers.insert_into_table(
        message.id, message.author.id, message.content, bot.db
    )
    log.info("Got message {}".format(message.id))
    log.info(message.attachments[0].proxy_url)

    bot_spam = message.guild.get_channel(backend.config.inktober_image_channel)

    my_message_id = await inktober_post(message, bot_spam)

    await backend.helpers.insert_into_message_origin_tracking(
        message.id, my_message_id.id, message.channel.id, bot.db
    )
    await backend.helpers.insert_original_id(
        my_message_id.id, message.id, message.channel.id, bot.db
    )


async def on_reaction_add_main(
    user: discord.Member,
    reaction: Union[discord.Reaction, discord.PartialEmoji],
    bot: Client,
    raw: bool,
    message: discord.Message = None,
):
    custom_emoji: bool

    if user == bot.user:
        return

    if raw:
        custom_emoji = reaction.is_custom_emoji()
        reaction_name = reaction_emoji = reaction.name
    else:
        custom_emoji = reaction.custom_emoji
        reaction_emoji = reaction.emoji
        if custom_emoji:
            reaction_name = reaction.emoji.name

    if raw:
        log.info("Is raw")
    else:
        log.info("Not raw")

    if not await backend.helpers.user_role_authed(user):
        if isinstance(reaction, discord.Reaction):
            log.info(
                "User not authed {} | {} {}".format(
                    user.id, user.display_name, reaction.message.id
                )
            )
        else:
            log.info(
                "User not authed {} | {} {}".format(
                    user.id, user.display_name, message.id
                )
            )
        return

    if not raw:
        message: discord.Message = reaction.message

    if await location_check(message):
        try:
            log.info(
                "{} {} {} ".format(
                    message.attachments,
                    custom_emoji,
                    reaction.emoji.name.lower()
                    in backend.config.inktober_custom_accept_emotes,
                )
            )
        except AttributeError:
            if isinstance(reaction, discord.Reaction):
                log.info("AE")
                log.info(
                    "{} {} {} ".format(
                        message.attachments,
                        custom_emoji,
                        reaction.emoji in backend.config.inktober_custom_accept_emotes,
                    )
                )
            else:
                log.info("AE")
                log.info(
                    "{} {} {} ".format(
                        message.attachments,
                        custom_emoji,
                        reaction.name in backend.config.inktober_custom_accept_emotes,
                    )
                )
        if message.attachments != []:
            if custom_emoji:
                if (
                    reaction_name.lower()
                    in backend.config.inktober_custom_accept_emotes
                ):
                    if not await backend.helpers.check_if_in_table(message.id, bot.db):
                        log.info("Added new inktober {}".format(message.id))
                        await new_inktober(message, bot)
                    else:
                        log.info("Message {} already in table".format(message.id))
        else:
            log.info("No attachments")

        if reaction_emoji in backend.config.date_buttons:
            log.info("Date buttons")
            if message.author == bot.user:
                now_embed: discord.Embed = message.embeds[0]
                now_time: datetime.datetime = now_embed.timestamp
                now_day = int(now_time.strftime("%d"))
                original_message_id, _ = await backend.helpers.grab_original_id(
                    message.id, bot.db
                )

                if reaction_emoji == "⏺":
                    day = now_day
                    await backend.helpers.insert_day(original_message_id, day, bot.db)
                    await message.add_reaction(
                        backend.config.inktober_lock_image_button
                    )

                elif reaction_emoji == "▶":
                    day = now_day + 1
                    await backend.helpers.insert_day(original_message_id, day, bot.db)
                    await message.add_reaction(
                        backend.config.inktober_lock_image_button
                    )

                elif reaction_emoji == "◀":
                    day = now_day - 1
                    if day == 0:
                        now: datetime.datetime = datetime.datetime.now()
                        year: int = int(now.strftime("%Y"))
                        month: int = int(now.strftime("%m"))
                        if month == 1:
                            month_data: tuple = calendar.monthrange(year, 12)
                        else:
                            month_data: tuple = calendar.monthrange(year, month - 1)
                        day = month_data[1]
                    await backend.helpers.insert_day(original_message_id, day, bot.db)
                    await message.add_reaction(
                        backend.config.inktober_lock_image_button
                    )

                else:
                    day = now_day
                    log.warning(
                        "How did this happen? {} | {}".format(
                            message.id, reaction_emoji
                        )
                    )

                message_to_update = message
                new_embed: discord.Embed = message_to_update.embeds[0]
                log.info(new_embed.to_dict())
                new_embed_embed = discord.Embed(
                    timestamp=new_embed.timestamp,
                    title="Day {} ({})".format(
                        str(day), backend.day_themes.day_themes[day]
                    ),
                    colour=15169815,
                )
                new_embed_embed.set_image(url=new_embed.image.url)
                new_embed_embed.set_author(
                    name=new_embed.author.name, icon_url=new_embed.author.icon_url
                )

                await message_to_update.edit(embed=new_embed_embed)
        elif reaction_emoji == backend.config.inktober_lock_image_button:
            day = await backend.helpers.fetch_day(message.id, bot.db)
            if day != "":
                log.info("Locking {}".format(message.id))
                try:
                    await message.clear_reactions()
                except discord.errors.Forbidden as Forbidden:
                    log.info("Forbidden from clearing reactions: {}".format(Forbidden))
                    for emoji in backend.config.all_inktober_buttons:
                        await message.remove_reaction(emoji, bot.user)
                except discord.errors.HTTPException as HTTP:
                    log.info("HTTPException: {}".format(HTTP))
                    for emoji in backend.config.all_inktober_buttons:
                        await message.remove_reaction(emoji, bot.user)

                intended_user = await backend.helpers.fetch_intended_user(
                    message.id, bot.db
                )
                intended_user: discord.Member = message.guild.get_member(intended_user)
                sheets_users = backend.sheets.sheets.fetch_users()
                if str(intended_user.id) in sheets_users:
                    old_days = backend.sheets.sheets.fetch_user_days(
                        str(intended_user.id), sheets_users
                    )
                    await backend.sheets.sheets.update_days(
                        str(intended_user.id), sheets_users, day, old_days, bot
                    )
                    if len(old_days[0].split(" ")) + 1 == 10:
                        await intended_user.add_roles(
                            message.guild.get_role(628014126953791498)
                        )
                        backend.sheets.sheets.say_that_roles_added(
                            str(intended_user.id), sheets_users
                        )
                else:
                    backend.sheets.sheets.insert_user_days(
                        intended_user.id,
                        sheets_users,
                        await backend.helpers.fetch_day(message.id, bot.db),
                        f"{intended_user.name}#{intended_user.discriminator}",
                    )
        else:
            log.info(
                "{} {}".format(
                    reaction_emoji == backend.config.inktober_lock_image_button,
                    reaction_emoji,
                )
            )
    else:
        log.info(
            "{} {}".format(
                message.guild.id == backend.config.inktober_server,
                message.channel.id in backend.config.inktober_authed_channels,
            )
        )


class OnReactionEvent(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        await on_reaction_add_main(user, reaction, self.bot, False)


def setup(bot):
    bot.add_cog(OnReactionEvent(bot))
