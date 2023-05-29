from typing import List

from src.NPCLLM import NPCLLM
from src.NPCMemory import NPCMemory
from src.ServerMsg import ServerMsg


class NPC:
    def __init__(
        self,
        personafile: str,
        memory_url: str,
        index_name: str,
    ) -> None:
        self.llm = NPCLLM.from_config(personafile)
        self.memory = NPCMemory(memory_url, index_name)
        self.chat_history: List[ServerMsg] = []

    def fill_messages(self, msglist: List[ServerMsg]) -> None:
        self.chat_history = msglist
        if self.memory is not None:
            self.memory.add_texts([str(msg) for msg in msglist])

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
