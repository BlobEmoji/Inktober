import discord
import backend.helpers

class OnMessageEditEvent:
    def __init__(self, bot):
        self.bot = bot

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            if before.server.id == "272885620769161216":
                if before.channel.id in ["493851049942319114", "411929226066001930"]:
                    if await backend.helpers.check_if_in_tracking_table(before.id, self.bot.db):
                        message_id_to_update, my_message_channel_id = await backend.helpers.fetch_from_tracking_table(before.id, self.bot.db)
                        my_channel = before.server.get_channel(my_message_channel_id)
                        message_to_update = await self.bot.get_message(my_channel, my_message_channel_id)
                        new_embed = message_to_update.embeds[0]
                        if len(after.content) <= 1024:
                            new_embed.set_field_at(new_embed.fields[0], "Message", after.content)
                        else:
                            new_embed.set_field_at(new_embed.fields[0], "Message", "{}...".format(after.content[:1021]))
                        await self.bot.edit_message(message_to_update, embed=new_embed)


def setup(bot):
    bot.add_cog(OnMessageEditEvent(bot))
