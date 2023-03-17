# Hello my minion
# I have become death the destoryer of worlds

import os
import discord
import openai
from dotenv import load_dotenv
from tony import Tony, TonyResponse

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_KEY')
openai.api_key = OPENAI_KEY

intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)
american = Tony(client=client, engine="text-davinci-003", temperature=0.6, frequency_penalty=0.3)


@client.event
async def on_ready():
    print('{0.user} here. anyone like lawns??? baba booey'.format(client))


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
        print("no response type determined, aborting")
        return
    
    # Response cleaning
    response = american.clean_response(response)
    
    try:
        await message.channel.send(response)
    except discord.HTTPException as e:
        print(e.args)
    print(f'MESSAGE: {message.content}')
    print(f'RESPONSE TYPE: {response_type}')
    print(f'RESPONSE: {response}')

# start the bot
client.run(TOKEN)
