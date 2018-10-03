import discord
import backend.helpers
import logging
import backend.day_themes
import backend.config
import discord.errors

log = logging.getLogger(__name__)


async def inktober_post(message: discord.Message, bot, bot_spam):
    embed = discord.Embed(timestamp=message.timestamp, colour=15169815)

    embed.set_image(url=message.attachments[0]["proxy_url"])
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    my_id = await bot.send_message(bot_spam, embed=embed)

    await bot.add_reaction(my_id, "◀")
    await bot.add_reaction(my_id, "⏺")
    await bot.add_reaction(my_id, "▶")

    return my_id


class OnReactionEvent:
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction: discord.Reaction, user):
        if reaction.message.server.id == "272885620769161216":
            if reaction.message.channel.id in ["493851049942319114", "411929226066001930"]:
                if reaction.message.attachments != []:
                    if await backend.helpers.user_role_authed(user):
                        if reaction.custom_emoji:
                            if reaction.emoji.name.lower() in ["greentick", "green_tick"]:
                                if not await backend.helpers.check_if_in_table(reaction.message.id, self.bot.db):
                                    await backend.helpers.insert_into_table(reaction.message.id,
                                                                            reaction.message.author.id,
                                                                            reaction.message.content, self.bot.db)
                                    log.info("Got message {}".format(reaction.message.id))
                                    log.info(reaction.message.attachments)
                                    log.info(reaction.message.attachments[0]["proxy_url"])

                                    bot_spam = reaction.message.server.get_channel(
                                        backend.config.inktober_image_channel)

                                    my_message_id = await inktober_post(reaction.message, self.bot, bot_spam)

                                    await backend.helpers.insert_into_message_origin_tracking(reaction.message.id,
                                                                                              my_message_id.id,
                                                                                              backend.config.inktober_image_channel,
                                                                                              self.bot.db)
                                    await backend.helpers.insert_original_id(my_message_id.id, reaction.message.id, backend.config.inktober_image_channel, self.bot.db)
                                else:
                                    log.info("Message {} already in table".format(reaction.message.id))
                else:
                    log.info("No attachments")
        if reaction.message.server.id == "272885620769161216":
            if reaction.message.channel.id in ["411929226066001930", "496422844012560398"]:
                if reaction.emoji in ["◀", "⏺", "▶"]:
                    log.info("Date buttons")
                    if reaction.message.author == self.bot.user:
                        if await backend.helpers.user_role_authed(user):
                            if await backend.helpers.fetch_day(reaction.message.id, self.bot.db) != "":
                                now_time = reaction.message.timestamp
                                now_day = int(now_time.strftime("%d"))
                                original_message_id, _ = await backend.helpers.grab_original_id(reaction.message.id, self.bot.db)

                                if reaction.emoji == "⏺":
                                    day = now_day
                                    await backend.helpers.insert_day(original_message_id, now_day, self.bot.db)
                                    await self.bot.add_reaction(reaction.message, "🔒")

                                elif reaction.emoji == "▶":
                                    day = now_day + 1
                                    await backend.helpers.insert_day(original_message_id, now_day + 1, self.bot.db)
                                    await self.bot.add_reaction(reaction.message, "🔒")

                                elif reaction.emoji == "◀":
                                    day = now_day - 1
                                    await backend.helpers.insert_day(original_message_id, now_day - 1, self.bot.db)
                                    await self.bot.add_reaction(reaction.message, "🔒")

                                else:
                                    day = now_day
                                    log.warning("How did this happen? {} | {}".format(reaction.message.id, reaction.emoji))

                                #my_message_id, my_message_channel_id = await backend.helpers.grab_original_id(reaction.message.id, self.bot.db)
                                # message_id_to_update, my_message_channel_id = await backend.helpers.fetch_from_tracking_table(
                                #    reaction.message.id, self.bot.db)

                                #my_channel = reaction.message.server.get_channel(str(my_message_channel_id))
                                #message_to_update = await self.bot.get_message(my_channel, my_message_id)
                                message_to_update = reaction.message
                                #log.info("{} {} {}".format(my_channel, my_message_id, message_to_update))
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
                elif reaction.emoji in ["🔒"]:
                    if user != self.bot.user:
                        log.info("{}".format(await backend.helpers.fetch_day(reaction.message.id, self.bot.db)))
                        if await backend.helpers.fetch_day(reaction.message.id, self.bot.db) != "":
                            log.info("Locking {}".format(reaction.message.id))
                            try:
                                await self.bot.clear_reactions(reaction.message)
                            except discord.errors.Forbidden as Forbidden:
                                log.info("Forbidden from clearing reactions: {}".format(Forbidden))
                                for emoji in ["◀", "⏺", "▶", "🔒"]:
                                    await self.bot.remove_reaction(reaction.message, emoji, self.bot.user)
                            except discord.errors.HTTPException as HTTP:
                                log.info("HTTPException: {}".format(HTTP))
                                for emoji in ["◀", "⏺", "▶", "🔒"]:
                                    await self.bot.remove_reaction(reaction.message, emoji, self.bot.user)


def setup(bot):
    bot.add_cog(OnReactionEvent(bot))
