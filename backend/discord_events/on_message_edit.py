import discord
import backend.helpers
import logging

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
                        log.info("In the channels")
                        message_id_to_update, my_message_channel_id = await backend.helpers.fetch_from_tracking_table(before.id, self.bot.db)
                        my_channel = before.server.get_channel(my_message_channel_id)
                        message_to_update = await self.bot.get_message(my_channel, my_message_channel_id)
                        new_embed = message_to_update.embeds[0]
                        if len(after.content) <= 1024:
                            new_embed.set_field_at(new_embed.fields[0], "Message", after.content)
                        else:
                            new_embed.set_field_at(new_embed.fields[0], "Message", "{}...".format(after.content[:1021]))
                        await self.bot.edit_message(message_to_update, embed=new_embed)
                    else:
                        log.info("not in the channels")


def setup(bot):
    bot.add_cog(OnMessageEditEvent(bot))
