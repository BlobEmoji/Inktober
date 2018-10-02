import discord
import backend.helpers
import logging
import discord.utils

log = logging.getLogger(__name__)


class OnMessageEditEvent:
    def __init__(self, bot):
        self.bot = bot

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            log.info("!=")
            if before.server.id == "272885620769161216":
                if before.channel.id in ["493851049942319114", "411929226066001930"]:
                    log.info("In the channels")
                    if await backend.helpers.check_if_in_tracking_table(before.id, self.bot.db):
                        log.info("Is tracked")
                        message_id_to_update, my_message_channel_id = await backend.helpers.fetch_from_tracking_table(before.id, self.bot.db)

                        my_channel = before.server.get_channel(str(my_message_channel_id))

                        message_to_update = await self.bot.get_message(my_channel, message_id_to_update)

                        new_embed = message_to_update.embeds[0]
                        log.info(new_embed)

                        if len(after.content) <= 1024:
                            new_embed_embed = discord.Embed(timestamp=discord.utils.parse_time(new_embed["timestamp"]),
                                                            description=after.content, title=new_embed["title"],
                                                            colour=15169815)

                        else:
                            new_embed_embed = discord.Embed(timestamp=discord.utils.parse_time(new_embed["timestamp"]),
                                                            description="{}...".format(after.content[:1021]),
                                                            title=new_embed["title"],
                                                            colour=15169815)

                        new_embed_embed.set_image(url=new_embed["image"]["url"])
                        new_embed_embed.set_author(name=new_embed["author"]["name"], icon_url=new_embed["author"]["icon_url"])
                        await self.bot.edit_message(message_to_update, embed=new_embed_embed)
                    else:
                        log.info("not in the channels")


def setup(bot):
    bot.add_cog(OnMessageEditEvent(bot))
