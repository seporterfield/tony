# When Alexander saw the breadth of his domain, he wept for there were no more worlds to conquer

import os
import discord
import openai
from dotenv import load_dotenv
import logging
from tony import Tony, TonyResponse

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_KEY')
openai.api_key = OPENAI_KEY

logger = logging.getLogger('discord')
discord_logger = logger.getChild('child')

intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)
american = Tony(client=client, engine="text-davinci-003", temperature=0.6, frequency_penalty=0.3)

@client.event
async def on_ready():
    discord_logger.info('{0.user} is now online.'.format(client))


@client.event
async def on_message(message: discord.Message):
        
    # Get response type
    response_type = await american.get_response_type(message)
    if response_type == TonyResponse.SILENCE:
        return

    # Get response
    response = ""
    if response_type != None and type(response_type) == TonyResponse:
        response = await american.prompt_tony(response_type, message)
    else:
        discord_logger.error("no response type determined, aborting")
        return
    
    # Response cleaning
    response = american.clean_response(response)
    
    try:
        await message.channel.send(response)
    except discord.HTTPException as e:
        discord_logger.info.error(e.args)
    discord_logger.info(f'RESPONSE TYPE: {response_type}')
    discord_logger.info(f'RESPONSE: {response}')
    discord_logger.info(f'MESSAGE: {message.content}')

# start the bot
client.run(TOKEN)
