import logging

import discord

from src.BaseClient import BaseClient
from src.ClientNPCController import ClientNPCController

logger = logging.getLogger("discord")
discord_logger = logger.getChild("child")


# Discord Client wrapper for turning events into function calls
class DiscordClient(BaseClient, discord.Client):
    def set_controller(self, controller: ClientNPCController):
        self.controller = controller

    def print_log(self, text: str):
        if self.user is None:
            raise discord.DiscordException("User not yet logged in.")
        discord_logger.info(f"{self.user.name} | {text}")

    async def on_ready(self):
        self.print_log(f"{self.user.display_name} is now online.")

    async def on_resumed(self):
        await self.controller.on_resumed()

    async def on_message(self, message: discord.Message):
        self.print_log(f"{message.author.name}: {message.content}")
        await self.controller.on_message(message)
