import discord
import backend.helpers
import logging

log = logging.getLogger(__name__)


async def inktober_post(message: discord.Message, bot, bot_spam):
    embed = discord.Embed(title="Inktober", timestamp=message.timestamp)
    embed.set_image(url=message.attachments[0]["proxy_url"])
    if message.content != "":
        if len(message.content) <= 1024:
            embed.add_field(name="Message", value=message.content)
        else:
            embed.add_field(name="Message", value="{}...".format(message.content[:1021]))
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    await bot.send_message(bot_spam, embed=embed)


class OnReactionEvent:
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction: discord.Reaction, user):
        if reaction.message.server.id == "272885620769161216":
            log.info("Is in blob")
            if reaction.message.channel.id in ["493851049942319114", "411929226066001930"]:
                log.info("channel")
                if reaction.message.attachments != []:
                    if await backend.helpers.user_role_authed(user):
                        if reaction.custom_emoji:
                            if reaction.emoji.name.lower() in ["greentick", "green_tick"]:
                                if not await backend.helpers.check_if_in_table(reaction.message.id, self.bot.db):
                                    await backend.helpers.insert_into_table(reaction.message.id,
                                                                            reaction.message.author.id, reaction.message.content, self.bot.db)
                                    log.info("Got message {}".format(reaction.message.id))
                                    log.info(reaction.message.attachments)
                                    log.info(reaction.message.attachments[0]["proxy_url"])

                                    bot_spam = reaction.message.server.get_channel("411929226066001930")

                                    await inktober_post(reaction.message, self.bot, bot_spam)
                                else:
                                    log.info("Message {} already in table".format(reaction.message.id))
                else:
                    log.info("No attachments")


def setup(bot):
    bot.add_cog(OnReactionEvent(bot))
