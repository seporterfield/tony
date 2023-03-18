import os
import discord
import openai
from dotenv import load_dotenv
import logging
from npc import NPC, NPCResponse
import asyncio

# Keys and environment vars
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_KEY')
openai.api_key = OPENAI_KEY

# Logging setup
logger = logging.getLogger('discord')
discord_logger = logger.getChild('child')

# Discord setup
intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)

NPC_TYPING_TIME = 4 # seconds between messages
NPC_READING_TIME = 7
lock = asyncio.Lock()

bot = NPC.from_yaml(filepath='src/tony.yaml', client=client, logger=logger)

@client.event
async def on_ready():
    # Once bot has logged in, send a status update
    discord_logger.info('{0.user} is now online.'.format(client))
    # Get recent chat history
    await bot.fill_messages()


@client.event
async def on_message(message: discord.Message):
    async with lock: # NPCs, unlike chatbots, answer in chronological order.
        # New message in server, update message queue
        bot.update_messages(message)
        discord_logger.info(f"{message.author.name}: {message.content}")
        # Get response type
        response_type = await bot.get_response_type()
        discord_logger.info(f"{response_type}")
        if response_type == NPCResponse.SILENCE:
            return
        
        # Get reply
        response = "..."
        try:
            response = await bot.prompt()
        except Exception as e:
            discord_logger.error(e.args)
        discord_logger.info(f"RESPONSE-PRECLEAN: {response}")
    
        # Remove text related to prompts and generation
        response = bot.clean_response(response)
        if response == "":
            return
        discord_logger.info(f"RESPONSE: {response}")
    
        # Send the message
        async with message.channel.typing():
            # "Typing..."
            await asyncio.sleep(NPC_TYPING_TIME)
        try:
            await message.channel.send(response)
        except Exception as e:
            discord_logger.error(e.args)
        
        # Waiting for others to send messages before updating queue
        await asyncio.sleep(NPC_READING_TIME)
            
# Start the bot!
client.run(TOKEN)
