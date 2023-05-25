import discord
import logging
from npc import DiscordNPC
from npc_llm import NPCLLM
import asyncio
import math

DISCORD_CHAR_LIMIT = 2000
# lock = asyncio.Lock()

# Logging setup
logger = logging.getLogger("discord")
discord_logger = logger.getChild("child")
# discord_logger.setLevel(logging.DEBUG)


# Discord client for NPC chatbots
class NPCClient(discord.Client):
    def __init__(
        self,
        command_prefix,
        intents,
        bot_config: str,
        typing_time: int,
        reading_time: int,
    ):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.typing_time = typing_time
        self.reading_time = reading_time
        self.responding = False
        self.bot = DiscordNPC(
            llm=NPCLLM.from_config(bot_config),
            user=self.user,
        )

    async def send_chunks(self, message: discord.Message, text_chunks):
        async with message.channel.typing():
            # "Typing..."
            await asyncio.sleep(self.typing_time)
        try:
            for chunk in text_chunks:
                await message.channel.send(chunk)
        except Exception as e:
            discord_logger.error(self.bot.name, e.args)

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
            response = await self.bot.prompt()
        except Exception as e:
            discord_logger.error(e.args)
        discord_logger.info(f"{self.bot.name}|RESPONSE-PRECLEAN: {response}")
        return response

    def message_chat(self, message):
        # Generate reply
        response = self.generate_reply(message)
        # Chunk response up into discord-message-size bits
        text_chunks = self.chunk_response(response)

        if response == "":
            self.responding = False
            return
        discord_logger.info(f"{self.bot.name}|RESPONSE: {response}")

        # Send the message
        self.send_chunks(message, text_chunks)

    async def on_ready(self):
        # Once bot has logged in, send a status update
        discord_logger.info("{0}|{1.user} is now online.".format(self.bot.name, self))
        # Get recent chat history
        await self.bot.fill_messages()

    async def on_message(self, message: discord.Message):
        if self.responding:
            return
        self.responding = True
        # New message in server, update message queue
        await self.bot.update_messages(message)
        discord_logger.info(f"{self.bot.name}|{message.author.name}: {message.content}")
        # Get response type
        respond: bool = await self.bot.respond_to_new_msg()
        discord_logger.info(f"{self.bot.name}|{'responding...' if respond else 'ignoring.'}")
        if respond:
            self.responding = False
            return
        # Message chat
        self.message_chat(message)

        # Waiting for others to send messages before updating queue
        await asyncio.sleep(self.reading_time)
        self.responding = False
