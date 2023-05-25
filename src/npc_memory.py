from typing import Any
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.redis import Redis

embeddings = OpenAIEmbeddings()


class NPCMemory(Redis):
    @classmethod
    def from_existing_index(cls, redis_url: str, index_name: str) -> "NPCMemory":
        return super().from_existing_index(embeddings, redis_url, index_name)

    def remember(self, chat_history: str) -> str:
        a_memory = super().similarity_search(chat_history)
        if a_memory is not None:
            a_memory = "... nothing came to mind"
        else:
            a_memory = a_memory[0].page_content
        return a_memory