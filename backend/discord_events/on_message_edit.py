import logging

import discord
import discord.utils
from discord.ext import commands

import backend.helpers
from bot import Bot as Client

log = logging.getLogger(__name__)


class OnMessageEditEvent(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            log.info("!=")
            if before.guild.id == "272885620769161216":
                if before.channel.id in ["493851049942319114", "411929226066001930"]:
                    log.info("In the channels")
                    if await backend.helpers.check_if_in_tracking_table(before.id, self.bot.db):
                        log.info("Is tracked")
                        message_id_to_update, my_message_channel_id = await backend.helpers.fetch_from_tracking_table(
                            before.id, self.bot.db)

                        my_channel = before.guild.get_channel(str(my_message_channel_id))

                        message_to_update = await my_channel.get_message(message_id_to_update)

                        new_embed = message_to_update.embeds[0]
                        log.info(new_embed)

                        new_embed_embed = discord.Embed(timestamp=discord.utils.parse_time(new_embed["timestamp"]),
                                                        title=new_embed["title"],
                                                        colour=15169815)

                        new_embed_embed.set_image(url=new_embed["image"]["url"])
                        new_embed_embed.set_author(name=new_embed["author"]["name"],
                                                   icon_url=new_embed["author"]["icon_url"])
                        await message_to_update.edit(embed=new_embed_embed)
                    else:
                        log.info("not in the channels")


def setup(bot):
    bot.add_cog(OnMessageEditEvent(bot))
