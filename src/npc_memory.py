from typing import List

from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis


class NPCMemory:
    def __init__(self, url: str, index_name: str):
        # TODO start memory with some news articles

        self.redis = Redis.from_documents(
            [Document(page_content="among us!")],
            OpenAIEmbeddings(),  # type: ignore[call-arg]
            redis_url="redis://localhost:6379",
            index_name="link",
        )

    def remember(self, chat_history: str) -> str:
        simsearch_result = self.redis.similarity_search(chat_history)
        return (
            simsearch_result[0].page_content
            if simsearch_result is not None and simsearch_result != []
            else "... nothing came to mind"
        )

    def add_texts(self, texts: List[str]) -> None:
        self.redis.add_texts(texts)
