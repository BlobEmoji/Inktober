import logging
import traceback

import discord
from discord.ext import commands

from bot import Bot as Client

log = logging.getLogger(__name__)


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot

    async def on_error(self, event, *args, **kwargs):
        log.warning(event)
        log.warning(*args)
        log.warning(**kwargs)

    async def on_command_error(
        self, context: commands.Context, exception: commands.CommandError
    ):
        error_server: discord.Guild = self.bot.get_guild(272885620769161216)
        error_channel: discord.TextChannel = error_server.get_channel(
            411929226066001930
        )
        context.message: discord.Message
        trace = traceback.format_exception(
            type(exception), exception, exception.__traceback__, limit=15
        )
        log.error("".join(trace))
        log.error(context.command)
        log.error(context.invoked_with)
        log.error(context.bot)
        log.error(context.args)
        if context.message.guild is not None:
            server = context.message.guild.name
        else:
            server = None
        await error_channel.send(
            "_ _\nInvoked With: {}\nArgs: {}\nServer: {}\nUser: {}\n```{}```".format(
                repr(context.invoked_with),
                repr(context.args),
                repr(server),
                repr(context.message.author.name),
                "".join(trace),
            )
        )


def setup(bot):
    bot.add_cog(Errors(bot))
