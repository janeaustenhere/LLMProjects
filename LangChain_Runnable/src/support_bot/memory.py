from threading import RLock
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

class SessionMemoryStore:
    """In-process memory : replace this class for persistent storage"""

    def __init__(self) -> None:
        self._session : dict[str, list[BaseMessage]] = {}
        self._lock : RLock = RLock()

    def history(self, session_id: str) -> list[BaseMessage]:
        with self._lock:
            return list(self._session.get(session_id,[]))


    def add_turn(self, session_id: str, user_text: str, assistant_text: str) -> None:
        with self._lock:
            session = self._session.setdefault(session_id,[])
            session.extend([HumanMessage(
                content=user_text),
                AIMessage(content=assistant_text)
            ])

            
    def clear(self, session_id: str) -> None:
        with self._lock:
            self._session.pop(session_id, None)