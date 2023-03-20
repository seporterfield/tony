import discord
import logging
from npc import NPC, NPCResponse
import asyncio
import math

DISCORD_CHAR_LIMIT=2000
#lock = asyncio.Lock()

# Logging setup
logger = logging.getLogger('discord')
discord_logger = logger.getChild('child')
# discord_logger.setLevel(logging.DEBUG)

class NPCClient(discord.Client):
    def __init__(self, command_prefix, intents, bot_config: str, typing_time: int, reading_time: int):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.typing_time = typing_time
        self.reading_time = reading_time
        self.responding = False
        self.bot = NPC.from_yaml(filepath=bot_config, client=self, logger=discord_logger)
    
    async def on_ready(self):
        # Once bot has logged in, send a status update
        discord_logger.info('{0}|{1.user} is now online.'.format(self.bot.name, self))
        # Get recent chat history
        await self.bot.fill_messages()
        
    async def on_message(self, message: discord.Message):
        if self.responding:
            return
        #async with lock: # NPCs, unlike chatbots, answer in chronological order.
        self.responding = True
        # New message in server, update message queue
        await self.bot.update_messages(message)
        discord_logger.info(f"{self.bot.name}|{message.author.name}: {message.content}")
        # Get response type
        response_type = await self.bot.get_response_type()
        discord_logger.info(f"{self.bot.name}|{response_type}")
        if response_type == NPCResponse.SILENCE:
            self.responding = False
            return
        
        # Get reply
        response = "..."
        try:
            response = await self.bot.prompt()
        except Exception as e:
            discord_logger.error(e.args)
        discord_logger.info(f"{self.bot.name}|RESPONSE-PRECLEAN: {response}")
    
        # Remove text related to prompts and generation
        response = self.bot.clean_response(response)
        # Chunk response up into discord-message-size bits
        text_chunks = []
        num_chunks = math.ceil(len(response)/float(DISCORD_CHAR_LIMIT))
        for chunk_idx in range(num_chunks):
            new_chunk = response[chunk_idx*DISCORD_CHAR_LIMIT:(chunk_idx+1)*DISCORD_CHAR_LIMIT]
            text_chunks.append(new_chunk)
            
        if response == "":
            self.responding = False
            return
        discord_logger.info(f"{self.bot.name}|RESPONSE: {response}")
    
        # Send the message
        async with message.channel.typing():
            # "Typing..."
            await asyncio.sleep(self.typing_time)
        try:
            for chunk in text_chunks:
                await message.channel.send(chunk)
        except Exception as e:
            discord_logger.error(self.bot.name, e.args)
        
        # Waiting for others to send messages before updating queue
        await asyncio.sleep(self.reading_time)
        self.responding = False
