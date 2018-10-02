import logging
import traceback
from discord.ext import commands

log = logging.getLogger(__name__)

startup_extensions = ["backend.discord_events.on_message", "backend.discord_events.on_reaction_add",
                      "backend.discord_events.on_message_edit"
                      "backend.command_checks", "backend.helpers"]


class ModuleLoader:
    def __init__(self, bot):
        self.bot = bot
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
    async def reload(self, ctx: commands.Context, extension: str):
        if ctx.message.author.id == "240973228632178689":
            """Reload extensions."""
            await self.backend(ctx, 'reload', extension)
        else:
            await self.bot.add_reaction(ctx.message, "\U0000274c")

    async def backend(self, ctx, action, extension):
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
            await self.bot.say(MNFE)
        except Exception as e:
            log.error("Failed to {} {}: {}".format(action, extension, e.__class__.__name__))

            await self.bot.say("```{}```".format(traceback.format_exc(limit=15)))
            await self.bot.add_reaction(ctx.message, "\U0000274c")
        else:
            await self.bot.add_reaction(ctx.message, "\U00002705")


def setup(bot):
    bot.add_cog(ModuleLoader(bot))
