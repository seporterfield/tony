import asyncio
import math
from typing import Any, List

import discord

from src.BaseClientHandler import BaseClientHandler
from src.DiscordClient import DiscordClient
from src.ServerMsg import ServerMsg

DISCORD_CHAR_LIMIT = 2000

MAX_CHAT_HISTORY = 10


# Discord client for NPC chatbots
class DiscordClientHandler(BaseClientHandler):
    def __init__(
        self,
        client: DiscordClient,
        typing_time: int,
    ):
        super().__init__(client, typing_time)
        self.client: DiscordClient = client
        self.replying = False

    # Connection

    def connect(self, token: str | None = None):
        if token is None:
            raise ValueError("No Discord token specified.")
        self.client.run(token=token)
        return

    # Event Based

    def on_ready(self) -> None:
        return None

    async def on_resumed(self, chat_history: List[ServerMsg]) -> discord.Message | None:
        # sourcery skip: assign-if-exp
        if self.client.user is None:
            return None
        if not chat_history:
            return None
        message = chat_history[0].original_message
        if not isinstance(message, discord.Message):
            raise TypeError(
                "Chat history contains messages not of type discord.Message"
            )
        await message.channel.send("**User back online after connection issues**")
        if message.author.id == self.client.user.id:
            return None
        return message

    async def on_message(self, message: discord.Message) -> discord.Message | None:
        return None

    # Other Functions

    async def send_chunks(self, channel: discord.abc.Messageable, text_chunks):
        async with channel.typing():
            # "Typing..."
            await asyncio.sleep(self.typing_time)
        try:
            for chunk in text_chunks:
                await channel.send(chunk)
        except Exception as e:
            print(e.with_traceback(e.__traceback__))

    def chunk_response(self, response):
        text_chunks = []
        num_chunks = math.ceil(len(response) / float(DISCORD_CHAR_LIMIT))
        for chunk_idx in range(num_chunks):
            new_chunk = response[
                chunk_idx * DISCORD_CHAR_LIMIT : (chunk_idx + 1) * DISCORD_CHAR_LIMIT
            ]
            text_chunks.append(new_chunk)
        return text_chunks

    async def message_channel(self, message_text: str, channel: Any = None):
        if self.client.user is None:
            return
        if channel is None:
            raise ValueError("No channel specified.")
        if not isinstance(channel, discord.abc.Messageable):
            raise TypeError("Channel is not of type discord.abc.Messageable.")

        # Chunk response up into discord-message-size bits
        text_chunks = self.chunk_response(message_text)
        self.client.print_log(f"RESPONSE: {message_text}")
        # Send the message
        await self.send_chunks(channel, text_chunks)

    async def should_reply_to_msg(self, message: discord.Message) -> bool:
        if self.client.user is None:
            return False
        # Direct @mentions or @everyone
        if self.client.user.mentioned_in(message) or message.mention_everyone:
            return True
        # Message replies to npc
        if message.reference is not None:
            referenced_msg_id = message.reference.message_id
            if referenced_msg_id is None:
                return False
            replied_msg = await message.channel.fetch_message(referenced_msg_id)
            if replied_msg.author.id == self.client.user.id:
                return True
        return False

    def get_message_channel(self, message: discord.Message):
        return message.channel

    async def get_chat_history(self, message: Any) -> List[ServerMsg]:
        if not isinstance(message, discord.Message):
            raise TypeError("Message is not of type discord.Message")
        chat_history = message.channel.history(limit=MAX_CHAT_HISTORY)
        return [
            ServerMsg.from_discord_message(message) async for message in chat_history
        ]

    def message_is_from_user(self, message: discord.Message) -> bool:
        if not isinstance(message, discord.Message):
            raise TypeError("Message is not of type discord.Message")
        if self.client.user is None:
            raise discord.DiscordException("User not yet logged in.")
        return message.author.id == self.client.user.id
