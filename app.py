import argparse
import os

import discord
import openai
from dotenv import load_dotenv

from src.npcclient import NPCClient

# Keys and environment vars
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_KEY


def parse_arguments():
    parser = argparse.ArgumentParser(description="NPC Chatbot")
    parser.add_argument(
        "--persona", type=str, required=True, help="Path to the persona YAML file"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Discord setup
    intents = discord.Intents.all()
    bot_client = NPCClient(
        command_prefix="!",
        intents=intents,
        personafile=args.persona,
        url="redis://localhost:6379",  # TODO configure testing vector db and add url
        index_name="persona",
        typing_time=4,
        reading_time=7,
    )
    bot_client.run(token=BOT_TOKEN)


if __name__ == "__main__":
    main()
