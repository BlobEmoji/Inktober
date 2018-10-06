import logging

import discord
import discord.errors

import backend.config
import backend.day_themes
import backend.helpers

log = logging.getLogger(__name__)


async def inktober_post(message: discord.Message, bot, bot_spam):
    embed = discord.Embed(timestamp=message.timestamp, colour=15169815)

    embed.set_image(url=message.attachments[0]["proxy_url"])
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    my_id = await bot.send_message(bot_spam, embed=embed)

    for emote in backend.config.date_buttons:
        await bot.add_reaction(my_id, emote)

    return my_id


async def location_check(message: discord.Message):
    if message.server.id == backend.config.inktober_server:
        log.info("Inktober server")
        if message.channel.id in backend.config.inktober_authed_channels:
            log.info("Inktober authed")
            return True
    return False


async def new_inktober(message: discord.Message, bot):
    await backend.helpers.insert_into_table(message.id,
                                            message.author.id,
                                            message.content, bot.db)
    log.info("Got message {}".format(message.id))
    log.info(message.attachments)
    log.info(message.attachments[0]["proxy_url"])

    bot_spam = message.server.get_channel(
        backend.config.inktober_image_channel)

    my_message_id = await inktober_post(message, bot, bot_spam)

    await backend.helpers.insert_into_message_origin_tracking(message.id,
                                                              my_message_id.id,
                                                              message.channel.id,
                                                              bot.db)
    await backend.helpers.insert_original_id(my_message_id.id, message.id,
                                             message.channel.id, bot.db)


class OnReactionEvent:
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction: discord.Reaction, user):
        if user == self.bot.user:
            return
        if not await backend.helpers.user_role_authed(user):
            log.info("User not authed {} {}".format(user.id, reaction.message.id))
            return

        message: discord.Message = reaction.message

        if await location_check(message):
            if message.attachments != []:
                if reaction.custom_emoji:
                    if reaction.emoji.name.lower() in backend.config.inktober_custom_accept_emotes:
                        if not await backend.helpers.check_if_in_table(message.id, self.bot.db):
                            await new_inktober(message, self.bot)
                        else:
                            log.info("Message {} already in table".format(message.id))
            else:
                log.info("No attachments")

            if reaction.emoji in backend.config.date_buttons:
                log.info("Date buttons")
                if message.author == self.bot.user:
                    now_time = message.timestamp
                    now_day = int(now_time.strftime("%d"))
                    original_message_id, _ = await backend.helpers.grab_original_id(message.id, self.bot.db)

                    if reaction.emoji == "⏺":
                        day = now_day
                        await backend.helpers.insert_day(original_message_id, now_day, self.bot.db)
                        await self.bot.add_reaction(message, backend.config.inktober_lock_image_button)

                    elif reaction.emoji == "▶":
                        day = now_day + 1
                        await backend.helpers.insert_day(original_message_id, now_day + 1, self.bot.db)
                        await self.bot.add_reaction(message, backend.config.inktober_lock_image_button)

                    elif reaction.emoji == "◀":
                        day = now_day - 1
                        await backend.helpers.insert_day(original_message_id, now_day - 1, self.bot.db)
                        await self.bot.add_reaction(message, backend.config.inktober_lock_image_button)

                    else:
                        day = now_day
                        log.warning("How did this happen? {} | {}".format(message.id, reaction.emoji))

                    message_to_update = message
                    new_embed = message_to_update.embeds[0]
                    log.info(new_embed)

                    new_embed_embed = discord.Embed(timestamp=discord.utils.parse_time(new_embed["timestamp"]),
                                                    title="Day {} ({})".format(str(day),
                                                                               backend.day_themes.day_themes[day]),
                                                    colour=15169815)
                    new_embed_embed.set_image(url=new_embed["image"]["url"])
                    new_embed_embed.set_author(name=new_embed["author"]["name"],
                                               icon_url=new_embed["author"]["icon_url"])

                    await self.bot.edit_message(message_to_update, embed=new_embed_embed)
            elif reaction.emoji == backend.config.inktober_lock_image_button:
                log.info("{}".format(await backend.helpers.fetch_day(message.id, self.bot.db)))
                if await backend.helpers.fetch_day(message.id, self.bot.db) != "":
                    log.info("Locking {}".format(message.id))
                    try:
                        await self.bot.clear_reactions(message)
                    except discord.errors.Forbidden as Forbidden:
                        log.info("Forbidden from clearing reactions: {}".format(Forbidden))
                        for emoji in backend.config.all_inktober_buttons:
                            await self.bot.remove_reaction(message, emoji, self.bot.user)
                    except discord.errors.HTTPException as HTTP:
                        log.info("HTTPException: {}".format(HTTP))
                        for emoji in backend.config.all_inktober_buttons:
                            await self.bot.remove_reaction(message, emoji, self.bot.user)


def setup(bot):
    bot.add_cog(OnReactionEvent(bot))
