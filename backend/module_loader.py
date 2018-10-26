import logging
import traceback
from bot import Bot as Client

from discord.ext import commands

log = logging.getLogger(__name__)

startup_extensions = ["backend.discord_events.on_message", "backend.discord_events.on_reaction_add",
                      "backend.discord_events.on_message_edit",
                      "backend.command_checks", "backend.helpers", "backend.errors"]


class ModuleLoader:
    def __init__(self, bot):
        self.bot: Client = bot
        self.setup()

    def setup(self):
        for extension in startup_extensions:
            try:
                self.bot.load_extension(extension)
                log.info("Loaded extension {}".format(extension))
            except Exception as E:
                exc = "{}: {}".format(type(E).__name__, E)
                log.error("Failed to load extension {}\n{}".format(extension, exc))

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, extension: str):
        if ctx.message.author.id == 240973228632178689:
            """Reload extensions."""
            await self.backend(ctx, 'reload', extension)
        else:
            await ctx.message.add_reaction("\U0000274c")

    async def backend(self, ctx: commands.Context, action, extension):
        """
        Handles the loading/reloading/unloading of extensions.

        Parameters
        ----------
        ctx : Context
            The commands context, used for sending error messages and confirming the command is done
        action : str
            Which action should be performed on the extensions
        extension : str
            Extension to do the action on
        """

        try:
            # load_extension / reload_extension / unload_extension
            method = getattr(self.bot, f'{action}_extension')

            method(extension)
            log.info(f'successfully {action}ed {extension}')
        except ModuleNotFoundError as MNFE:
            log.info(MNFE)
            await ctx.send(MNFE)
        except Exception as e:
            log.error("Failed to {} {}: {}".format(action, extension, e.__class__.__name__))

            await ctx.send("```{}```".format(traceback.format_exc(limit=15)))
            await ctx.message.add_reaction("\U0000274c")
        else:
            await ctx.message.add_reaction("\U00002705")


def setup(bot):
    bot.add_cog(ModuleLoader(bot))
