from threading import RLock

from langchain_core.messages import BaseMessage

from app.domain import ConversationStore

class InMemoryConversationStore(ConversationStore):

    def __init__(self, max_messages: int) -> None:
        self._max_messages = max_messages
        self._data : dict[str, list[BaseMessage]] = {}
        self._lock = RLock()

    def get(self, conversation_id: str) -> list[BaseMessage]:
        with self._lock:
            return list(self._data.get(conversation_id, []))

    def append(self, conversation_id: str, messages: list[BaseMessage]) -> None:
        with self._lock:
            history = self._data.get(conversation_id, [])
            history.extend(messages)
            self._data[conversation_id] = history[-self._max_messages:]

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._data.pop(conversation_id, None)



