class on_reaction_event:
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, message):
        pass


def setup(bot):
    bot.add_cog(on_reaction_event)
