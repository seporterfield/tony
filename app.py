import argparse
import os

import discord
import openai
from dotenv import load_dotenv

from src.ClientNPCController import ClientNPCController
from src.DiscordClient import DiscordClient
from src.DiscordClientHandler import DiscordClientHandler
from src.NPC import NPC

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

    # Discord client setup
    intents = discord.Intents.all()
    client_handler = DiscordClientHandler(
        DiscordClient(
            command_prefix="!",
            intents=intents,
        ),
        typing_time=4,
    )

    # NPC includes persona, LLM/prompts, and memory
    npc = NPC(
        personafile=args.persona,
        memory_url="redis://localhost:6379",  # TODO configure testing vector db and add url
        index_name="persona",
    )

    # Controller handles main logic
    controller = ClientNPCController(client_handler, npc, reading_time=7.0)
    client_handler.set_controller(controller)

    # Start client
    client_handler.connect(token=BOT_TOKEN)


if __name__ == "__main__":
    main()
