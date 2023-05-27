import asyncio
import logging
import math
from typing import Optional

import discord

from src.discord_npc import DiscordNPC
from src.npc_llm import NPCLLM
from src.npc_memory import NPCMemory

DISCORD_CHAR_LIMIT = 2000
# lock = asyncio.Lock()

# Logging setup
logger = logging.getLogger("discord")
discord_logger = logger.getChild("child")


# Discord client for NPC chatbots
class NPCClient(discord.Client):
    def __init__(
        self,
        command_prefix,
        intents,
        personafile: str,
        url: str,
        index_name: str,
        typing_time: int,
        reading_time: int,
    ):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.typing_time = typing_time
        self.reading_time = reading_time
        self.responding = False
        self.bot = DiscordNPC(
            llm=NPCLLM.from_config(personafile),
            memory=NPCMemory(url, index_name),
        )

    async def send_chunks(self, channel: discord.abc.Messageable, text_chunks):
        async with channel.typing():
            # "Typing..."
            await asyncio.sleep(self.typing_time)
        try:
            for chunk in text_chunks:
                await channel.send(chunk)
        except Exception as e:
            discord_logger.error(e.with_traceback(e.__traceback__))

    def chunk_response(self, response):
        text_chunks = []
        num_chunks = math.ceil(len(response) / float(DISCORD_CHAR_LIMIT))
        for chunk_idx in range(num_chunks):
            new_chunk = response[
                chunk_idx * DISCORD_CHAR_LIMIT : (chunk_idx + 1) * DISCORD_CHAR_LIMIT
            ]
            text_chunks.append(new_chunk)
        return text_chunks

    async def generate_reply(self):
        # Get reply
        response = "..."
        try:
            response = self.bot.get_npc_response()
        except Exception as e:
            discord_logger.error(e.with_traceback(e.__traceback__))
        return response

    async def message_chat(self, channel: Optional[discord.abc.Messageable]):
        if channel is None:
            raise ValueError("No channel specified.")
        # Generate reply
        response = await self.generate_reply()
        # Chunk response up into discord-message-size bits
        text_chunks = self.chunk_response(response)

        username = "Unknown User" if self.user is None else self.user.name
        discord_logger.info(f"{username}|RESPONSE: {response}")

        # Send the message
        await self.send_chunks(channel, text_chunks)

    async def on_ready(self):
        # Once bot has logged in, send a status update
        discord_logger.info(f"{self.user.name}|{self.user.display_name} is now online.")
        # Pass user to bot now that we are logged in (otherwise methods return None)
        self.bot.user = self.user

    async def on_message(self, message: discord.Message):
        if not self.is_ready():
            return
        if self.user is None:
            raise discord.DiscordException("User agent not yet logged in.")
        if self.responding:
            return
        self.responding = True
        # New message in server, update message queue
        await self.bot.update_message_history(message)
        discord_logger.info(
            f"{self.user.name}|{message.author.name}: {message.content}"
        )
        # Get response type
        respond: bool = await self.bot.should_respond_to_new_msg(message)
        discord_logger.info(
            f"{self.user.name}|{'responding...' if respond else 'message ignored'}"
        )
        if not respond:
            self.responding = False
            return
        # Message chat
        await self.message_chat(message.channel)

        # Waiting for others to send messages before updating queue
        await asyncio.sleep(self.reading_time)
        self.responding = False
