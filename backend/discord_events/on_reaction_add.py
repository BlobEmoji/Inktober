import discord
import backend.helpers
import logging

log = logging.getLogger(__name__)


class on_reaction_event:
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction: discord.Reaction, user):
        log.info(reaction, user)
        if reaction.message.server.id == "272885620769161216":
            log.info("Is in blob")
            if reaction.message.channel.id == "493851049942319114":
                log.info("channel")
                if await backend.helpers.user_role_authed(user):
                    if reaction.custom_emoji:
                        if reaction.emoji.name.lower() in ["greentick", "green_tick"]:
                            log.info("Got message {}".format(reaction.message.id))
                            log.info(reaction.message.attachments)
                            log.info(reaction.message.attachments[0].proxy_url)


def setup(bot):
    bot.add_cog(on_reaction_event)
