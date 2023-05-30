from typing import List

from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis

NUM_MEMORIES = 3


class NPCMemory:
    def __init__(
        self, memory_url: str = "redis://localhost:6379", index_name: str = "link"
    ):
        # TODO start memory with some news articles
        try:
            self.redis = Redis.from_existing_index(
                OpenAIEmbeddings(), redis_url=memory_url, index_name=index_name  # type: ignore[call-arg]
            )
        except ValueError:
            self.redis = Redis.from_documents(
                [Document(page_content="Welcome! This is your memory palace.")],
                OpenAIEmbeddings(),  # type: ignore[call-arg]
                redis_url=memory_url,
                index_name=index_name,
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
