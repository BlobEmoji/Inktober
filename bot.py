import datetime
import logging

import asyncpg
import discord
from discord.ext import commands

import backend.config
import backend.logging


class Bot(commands.Bot):
    def __init__(self, command_prefix, **options):
        self.db = None
        super().__init__(command_prefix, **options)

    def reload_extension(self, name: str):
        self.unload_extension(name)
        self.load_extension(name)

    async def start(self, *args, **kwargs):
        self.db = await asyncpg.create_pool(user="postgres", host="inktober_postgres")
        await super().start(*args, **kwargs)


inktober: Bot = Bot(command_prefix="bb!",
                    owner_id=240973228632178689)


@inktober.event
async def on_ready():
    log.info("On rewrite")
    log.info(f"Connected at {datetime.datetime.now().strftime('%d %H:%M:%S')}")
    log.info(f"Logged in as {inktober.user.name} {inktober.user.id}")
    log.info("Connected to: ")

    for server in inktober.guilds:
        log.info(server.name)

    await inktober.change_presence(activity=discord.Game(name="Haunting blobkind"), status=None, afk=False)


if __name__ == "__main__":
    with backend.logging.setup_logging():
        log = logging.getLogger(__name__)

        try:
            inktober.load_extension("backend.module_loader")
        except Exception as E:
            exc = "{}: {}".format(type(E).__name__, E)
            log.error("Failed to load extension {}\n{}".format("backend.module_loader", exc))

    inktober.run(backend.config.discord_token)
