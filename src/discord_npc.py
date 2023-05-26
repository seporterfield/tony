from src.npc_llm import NPCLLM
from src.npc_memory import NPCMemory
from src.server_msg import ServerMsg
from typing import List
import discord

MAX_CHAT_HISTORY = 10

class DiscordNPC:

    name: str

    def __init__(self, user: discord.User, llm: NPCLLM, memory: NPCMemory) -> None:
        self.user: discord.User = user
        self.llm: NPCLLM = llm
        self.memory: NPCMemory = memory
        self.chat_history = []

    async def fill_messages(self, channel: discord.TextChannel) -> None:
        # sourcery skip: raise-specific-error
        if channel is None:
            raise Exception("No channel provided") # TODO add specific exception
        # channel.history() returns newest to oldest
        msglist = [ServerMsg.from_message(message) async for message in channel.history(limit=MAX_CHAT_HISTORY)]
        self.chat_history = msglist

    def get_npc_response(self, message_history: List[ServerMsg]) -> str:
        # Combine recent chat history into string
        message_history_str = "\n".join(
            [str(message) for message in reversed(message_history)]
        )
        # Get a relevant memory from long term memory
        a_memory = self.memory.remember(message_history_str)
        # Make prompt
        return self.llm.prompt(message_history_str, a_memory)

    def update_message_history(self, message: discord.Message):
        if len(self.chat_history) == 0:
            self.fill_messages(channel=message.channel)
        else:
            self.chat_history.insert(0, ServerMsg.from_message(message))
            self.memory.add_texts([self.chat_history.pop()])

    async def respond_to_new_msg(self) -> bool:
        # TODO implement this
        return True
