# When Alexander saw the breadth of his domain, he wept for there were no more worlds to conquer

import os
import discord
import openai
from dotenv import load_dotenv
import logging
from npc import NPC, NPCResponse
import asyncio

# Keys and environment vars\
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

NPC_TYPING_TIME = 12 # seconds between messages
lock = asyncio.Lock()

tony = NPC(name='Tony DeSalvo',
           username='TonyPatriot447',
           age=52,
           gender='man',
           setting='Long Island',
           job='landscaper',
           personality=['Italian-American', 'Trump lover', 'patriotic', 'easygoing',
            'hard-working', 'loves wine', 'into grilling',
            'lawnmower expert', 'casual and rough', 'slightly buzzed'],
           context=['love-hate relationship with his wife Angie',
                    'two kids, Tony Jr. and Dino, always on their iPads',
                    'watches Fox News daily', 'his son Dino told him about Discord'],
           client=client,
           history_length=5,
           model="gpt-3.5-turbo-0301",
           temperature=0.6,
           frequency_penalty=0.3,
           logger=logger)

@client.event
async def on_ready():
    # Once bot has logged in, send a status update
    discord_logger.info('{0.user} is now online.'.format(client))
    # Get recent chat history
    await tony.fill_messages()


@client.event
async def on_message(message: discord.Message):
    async with lock:
        # New message in server, update message queue
        tony.update_messages(message)
        discord_logger.info(f"{message.author.name}: {message.content}")
        # What kind of response do we need to give?
        response_type = await tony.get_response_type()
        discord_logger.info(f"{response_type}")
        if response_type == NPCResponse.SILENCE:
            return
        
        # "Typing..."
        async with message.channel.typing():
            await asyncio.sleep(NPC_TYPING_TIME)
        
        # With what words will we reply?
        response = "bababooey"
        try:
            response = await tony.prompt()
        except Exception as e:
            discord_logger.error(e.args)
        discord_logger.info(f"RESPONSE-PRECLEAN: {response}")
    
        # Remove text related to prompts and generation
        response = tony.clean_response(response)
        if response == "":
            return
        discord_logger.info(f"RESPONSE: {response}")
    
        # Send the message
        
        try:
            await message.channel.send(response)
        except Exception as e:
            discord_logger.error(e.args)
# Start the bot!
client.run(TOKEN)
