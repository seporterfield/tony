from typing import List, Optional

import discord

from src.npc_llm import NPCLLM
from src.npc_memory import NPCMemory
from src.server_msg import ServerMsg

MAX_CHAT_HISTORY = 10


class DiscordNPC:
    def __init__(
        self,
        llm: NPCLLM,
        memory: Optional[NPCMemory] = None,
        user: Optional[discord.User] = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.chat_history: List[ServerMsg] = []
        self.user = user

    async def fill_messages(self, channel: discord.abc.Messageable) -> None:
        # sourcery skip: raise-specific-error
        if channel is None:
            raise Exception("No channel provided")  # TODO add specific exception
        # channel.history() returns newest to oldest
        msglist = [
            ServerMsg.from_message(message)
            async for message in channel.history(limit=MAX_CHAT_HISTORY)
        ]
        self.chat_history = msglist

    def get_npc_response(self) -> str:
        # Combine recent chat history into string
        message_history_str = "\n".join(
            [str(message) for message in reversed(self.chat_history)]
        )
        # Get a relevant memory from long term memory
        a_memory = (
            self.memory.remember(message_history_str)
            if self.memory is not None
            else "... nothing came to mind"
        )
        # Make prompt
        return self.llm.prompt(message_history_str, a_memory)

    async def update_message_history(self, message: discord.Message) -> None:
        if len(self.chat_history) == 0:
            await self.fill_messages(channel=message.channel)
        else:
            self.chat_history.insert(0, ServerMsg.from_message(message))
            if self.memory is not None:
                self.memory.add_texts([str(self.chat_history.pop())])

    async def should_respond_to_new_msg(self, message: discord.Message) -> bool:
        if self.user is None:
            return False
        # Direct @mentions or @everyone
        if self.user.mentioned_in(message) or message.mention_everyone:
            return True
        # Message replies
        if message.reference is not None:
            referenced_msg_id = message.reference.message_id
            if referenced_msg_id is None:
                return False
            replied_msg = await message.channel.fetch_message(referenced_msg_id)
            if replied_msg.author.id == self.user.id:
                return True
        return False
