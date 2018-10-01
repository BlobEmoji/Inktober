import logging

log = logging.getLogger(__name__)

startup_extensions = ["backend.discord_events.on_message", "backend.discord_events.on_reaction_add",
                      "backend.command_checks"]


class Module_Loader:
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


def setup(bot):
    bot.add_cog(Module_Loader(bot))
