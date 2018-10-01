class on_message_event:
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        pass


def setup(bot):
    bot.add_cog(on_message_event(bot))
