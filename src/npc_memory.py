from typing import List

from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis

NUM_MEMORIES = 3


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
        simsearch_results = self.redis.similarity_search(chat_history)
        return (
            "...".join([result.page_content for result in simsearch_results])
            if simsearch_results is not None and len(simsearch_results) != NUM_MEMORIES
            else "... nothing came to mind"
        )

    def add_texts(self, texts: List[str]) -> None:
        self.redis.add_texts(texts)
