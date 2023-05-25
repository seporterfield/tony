from persona import Persona
from npc_llm import NPCLLM
import discord

class DiscordNPC:

    name: str

    def __init__(self, user: discord.User, llm: NPCLLM):
        self.user: discord.User = user
        self.llm: NPCLLM = llm

    def prompt(self):
        # Prep inputs from persona
        # Get response from langchain
        pass

    async def fill_messages(self):
        # Get messages from user.channel
        # Fill langchain conversation
        # Fill embeddings store
        pass

    async def update_messages(self, message):
        # Add message to langchain conversation
        # Add message to embeddings store
        pass

    async def respond_to_new_msg(self) -> bool:
        # Bool now
        pass
