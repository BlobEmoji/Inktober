import logging
import traceback

import discord
from discord.ext import commands

from bot import Bot as Client

log = logging.getLogger(__name__)


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        ctx.message: discord.Message
        error_server: discord.Guild = self.bot.get_guild(404070984769994753)
        error_channel: discord.TextChannel = error_server.get_channel(404074085522472961)

        trace = traceback.format_exception(type(error), error, error.__traceback__, limit=15)
        log.error("".join(trace))
        log.error(ctx.command)
        log.error(ctx.invoked_with)
        log.error(ctx.bot)
        log.error(ctx.args)
        if ctx.guild is not None:
            server = ctx.guild.name
            server_id = ctx.guild.id
            channel_id = ctx.channel.id
        else:
            server = None
            server_id = None
            channel_id = None
        await error_channel.send(
            "_ _\nInvoked With: {}\nArgs: {}\nServer: {} {}\nChannel: {}\nUser: {}#{} {}\n```{}```".format(
                repr(ctx.invoked_with),
                repr(ctx.args),
                repr(server),
                repr(server_id),
                repr(channel_id),
                repr(ctx.author.name),
                ctx.author.discriminator,
                repr(ctx.author.id),
                "".join(trace)))


def setup(bot):
    bot.add_cog(Errors(bot))
