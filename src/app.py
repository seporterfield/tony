from dotenv import load_dotenv
import os
import openai
import discord
from npcclient import NPCClient

# import asyncio
# from multiprocessing.context import Process

# Keys and environment vars
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY


def main():
    # Discord setup
    intents = discord.Intents.all()
    bot_client = NPCClient(
        command_prefix="!",
        intents=intents,
        bot_config="bot.yaml",
        typing_time=4,
        reading_time=7,
    )
    bot_client.run(token=BOT_TOKEN)


if __name__ == "__main__":
    main()
