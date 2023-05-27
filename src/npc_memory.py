from langchain.vectorstores.redis import Redis


class NPCMemory(Redis):
    def remember(self, chat_history: str) -> str:
        simsearch_result = super().similarity_search(chat_history)
        return (
            simsearch_result[0].page_content
            if simsearch_result is not None and simsearch_result != []
            else "... nothing came to mind"
        )
