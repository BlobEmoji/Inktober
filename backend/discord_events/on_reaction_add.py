import calendar
import datetime
import logging
from typing import Union, List, Set

import discord
import discord.errors
from discord.ext import commands

import backend.config
import backend.day_themes
import backend.helpers
import backend.sheets.sheets
from bot import Bot as Client

log = logging.getLogger(__name__)


async def inktober_post(message: discord.Message, bot_spam: discord.TextChannel, proxy_url: str) -> discord.Message:
    """
    Posts new Inktober post to the gallery channel specified in the Config

    :param message: discord.Message
    :param bot_spam: discord.TextChannel
    :param proxy_url: str
    :return: discord.Message
    """
    embed: discord.Embed = discord.Embed(timestamp=message.created_at, colour=15169815)
    message.attachments[0]: discord.Attachment

    embed.set_image(url=proxy_url)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    new_message = await bot_spam.send(embed=embed)

    for emote in backend.config.date_buttons:
        await new_message.add_reaction(emote)

    return new_message


async def location_check(message: discord.Message) -> bool:
    """
    Check to see if the message is sent in both a valid server & in a valid channel for Inktober

    :param message: discord.Message
    :return: bool
    """
    if message.guild.id == backend.config.inktober_server:
        if message.channel.id in backend.config.inktober_authed_channels:
            log.info("Inktober authed")
            return True
    return False


async def handle_lock(intended_user: discord.Member, sheets_users: list, day: str, bot, message):
    """
    Handles the processing of a locked message by either updating the data on G-Sheets in regards to days
    and adding roles if that check is valid, or  by adding the user to the sheet in the first place

    :param intended_user:
    :param sheets_users:
    :param day:
    :param bot:
    :param message:
    """
    if str(intended_user.id) in sheets_users:
        log.info(f"Fetching old days for {intended_user.id}")
        old_days = backend.sheets.sheets.fetch_user_days(str(intended_user.id), sheets_users)
        log.info(f"Updating days for {intended_user.id}")
        await backend.sheets.sheets.update_days(str(intended_user.id), sheets_users, day, old_days, bot)
        log.info(f"Fetching new days for {intended_user.id}")
        new_days = backend.sheets.sheets.fetch_user_days(str(intended_user.id), sheets_users)
        parsed_data = convert_to_unique_days(new_days[0].split(" "))
        if len(parsed_data) == 4:
            log.info(f"Added role to {intended_user.id}")
            await intended_user.add_roles(message.guild.get_role(761078728515518484))
            backend.sheets.sheets.say_that_roles_added(str(intended_user.id), sheets_users)
    else:
        backend.sheets.sheets.insert_user_days(
            intended_user.id,
            sheets_users,
            await backend.helpers.fetch_day(message.id, bot.db),
            f"{intended_user.name}#{intended_user.discriminator}",
        )


def convert_to_unique_days(list_of_days: List[int]) -> Set[str]:
    """
    Convert a list of ints (days) into their named equivalents & return a unique list

    :param list_of_days: List[int]
    :return: Set[str]
    """
    converted_list = []
    for day in list_of_days:
        converted_list.append(backend.day_themes.day_themes[day])

    return set(converted_list)


async def new_inktober(message: discord.Message, bot: Client):
    """
    Handler for all of the New Inktober logic such as backend & posting

    :param message: discord.Message
    :param bot: Client
    """

    proxy_url: str
    if len(message.attachments) > 0:
        proxy_url = message.attachments[0].proxy_url
        log.info(message.attachments[0].proxy_url)
    else:
        proxy_url = message.embeds[0].url
        if not proxy_url.endswith((".png", "jpg")):
            log.warning(f"Warning: {proxy_url} for {message} doesn't appear to be a valid Image URL")
            return

    log.info("Added new inktober {}".format(message.id))
    await backend.helpers.insert_into_table(
        message.id, message.author.id, message.content, bot.db
    )
    log.info("Got message {}".format(message.id))

    gallery_channel = message.guild.get_channel(backend.config.inktober_gallery_channel)

    my_message_id = await inktober_post(message, gallery_channel, proxy_url)

    await backend.helpers.insert_into_message_origin_tracking(
        message.id, my_message_id.id, message.channel.id, bot.db
    )
    await backend.helpers.insert_original_id(
        my_message_id.id, message.id, message.channel.id, bot.db
    )


def reaction_logging(attachment: List[discord.Attachment], custom_emoji, reaction) -> None:
    """
    Just logging of stuff, unsure why I did this

    :param attachment: List[discord.Attachment]
    :param custom_emoji:
    :param reaction:
    """
    try:
        log.info(
            "{} {} {} ".format(
                attachment,
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
                    attachment,
                    custom_emoji,
                    reaction.emoji in backend.config.inktober_custom_accept_emotes,
                )
            )
        else:
            log.info("AE")
            log.info(
                "{} {} {} ".format(
                    attachment,
                    custom_emoji,
                    reaction.name in backend.config.inktober_custom_accept_emotes,
                )
            )


async def cleanup_reactions(message: discord.Message, user: discord.ClientUser) -> None:
    """
    Cleanup reactions (control buttons) from a message that was sent

    :param message: discord.Message
    :param user: discord.ClientUser
    """
    try:
        await message.clear_reactions()
    except discord.errors.Forbidden as Forbidden:
        log.warning("Forbidden from clearing reactions: {}".format(Forbidden))
        for emoji in backend.config.all_inktober_buttons:
            await message.remove_reaction(emoji, user)
    except discord.errors.HTTPException as HTTP:
        log.warning("HTTPException: {}".format(HTTP))
        for emoji in backend.config.all_inktober_buttons:
            await message.remove_reaction(emoji, user)


async def on_reaction_add_main(
    user: discord.Member,
    reaction: Union[discord.Reaction, discord.PartialEmoji],
    bot: Client,
    raw: bool,
    message: discord.Message = None,
):
    """
    Main giant handle function for all logic dealing with adding reactions, both via on_reaction_add and the non cached
    on_reaction_add_raw
    :param user: discord.Member
    :param reaction: Union[discord.Reaction, discord.PartialEmoji]
    :param bot: Client
    :param raw: bool
    :param message: discord.Message
    :return:
    """
    custom_emoji: bool

    # Ignore bot/self
    if user == bot.user:
        return

    # If the message is raw, figure out basic logic of the emote used
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

    # If the user who reacted is not authorised to interact with the bot, reject them
    if not await backend.helpers.user_role_authed(user):
        return

    if not raw:
        message: discord.Message = reaction.message

    # If the message is from a valid location
    if await location_check(message):
        reaction_logging(message.attachments, custom_emoji, reaction)

        # If its a custom emoji
        if custom_emoji:
            if len(message.attachments) > 0 or len(message.embeds) > 0:
                # If it is a green tick
                if reaction_name.lower() in backend.config.inktober_custom_accept_emotes:
                    if not await backend.helpers.check_if_in_table(message.id, bot.db):
                        await new_inktober(message, bot)
                    else:
                        log.info("Message {} already in table".format(message.id))
            else:
                log.info("No attachments AND embeds")

        if reaction_emoji in backend.config.date_buttons:
            log.info("Date buttons")
            if message.author == bot.user:
                now_embed: discord.Embed = message.embeds[0]
                now_time: datetime.datetime = now_embed.timestamp
                now_day = int(now_time.strftime("%d"))
                original_message_id, _ = await backend.helpers.grab_original_id(
                    message.id, bot.db
                )

                # Logic for what date button was pressed, current, next, previous

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
                await cleanup_reactions(message, bot.user)

                intended_user = await backend.helpers.fetch_intended_user(
                    message.id, bot.db
                )
                intended_user: discord.Member = await message.guild.fetch_member(intended_user)
                sheets_users = backend.sheets.sheets.fetch_users()
                await handle_lock(intended_user, sheets_users, day, bot, message)
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
