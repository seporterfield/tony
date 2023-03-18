# When Alexander saw the breadth of his domain, he wept for there were no more worlds to conquer

import os
import discord
import openai
from dotenv import load_dotenv
import time
import logging
from npc import NPC, NPCResponse

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
           model="gpt-3.5-turbo",
           temperature=0.6,
           frequency_penalty=0.3,
           logger=logger)

@client.event
async def on_ready():
    # Once bot has logged in, send a status update
    discord_logger.info('{0.user} is now online.'.format(client))


@client.event
async def on_message(message: discord.Message):
    # New message in server, update message queue
    await tony.update_messages(message)
    logger.info(f"{message.author.name}: {message.content}")
    # What kind of response do we need to give?
    response_type = tony.get_response_type()
    logger.info(f"RESPONSE TYPE: {response_type}")
    if response_type == NPCResponse.SILENCE:
        return
    
    # With what words will we reply?
    response = "bababooey"
    try:
        response = tony.prompt()
    except Exception as e:
        discord_logger.error(e.args)
    
    # Remove text related to prompts and generation
    response = tony.clean_response(response)
    if response == "":
        return
    logger.info(f"RESPONSE: {response}")
    
    # Send the message
    
    try:
        await message.channel.send(response)
    except Exception as e:
        discord_logger.error(e.args)
    discord_logger.info(f'MESSAGE: {message.content}\nRESPONSE TYPE: {response_type}\nRESPONSE: {response}')

# Start the bot!
client.run(TOKEN)
