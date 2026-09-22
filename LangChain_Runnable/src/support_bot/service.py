from unicodedata import category

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from .memory import SessionMemoryStore
from .config import Configs
from .models import TriageResult


class SupportService:
    """Coordinates LangChain triage , reply generaiton and session memory"""

    def __init__(self)->None:
        config = Configs.load()
        llm_options = {
            "api_key": config.api_key,
            "model": config.model,
            "temperature": config.temperature,
        }
        self._llm = ChatOpenAI(**llm_options)
        self._memory = SessionMemoryStore()
        self._triage_chain = self._build_triage_chain()
        self._reply_chain = self._build_reply_chain()


    def _build_triage_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Classify the message into exactly one category:"
                "policy_violation , genuine_defect, or other. Then assign a priority:"
                "High, Medium, or Low. Return only category, priority."

            ),
            ("human", "{ticket_text}")
        ])
        return prompt | self._llm | StrOutputParser() | RunnableLambda(self._parse_triage)

    @staticmethod
    def _parse_triage(raw:str) -> TriageResult:
        category, _, priority = raw.lower().partition(" ")
        category = category.strip()
        priority = priority.strip()
        allowed_categories = ["policy_violation", "genuine_defect", "other"]
        allowed_priority = ["high", "medium", "low"]
        return TriageResult(
            category = category if category in allowed_categories else "other",
            priority = priority if priority in allowed_priority else "Medium",
        )

    def _build_reply_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "you are a helpful Hopscotch customer-support assistant."
                "Only assist with Hopscotch purchase related queries"
                "use the internal ticket assessment to adjust your tone: genuinely defective"
                "item need a sincere apology plus a replacement or refund option : policy issues"
                "need a warm explanation of the policy. Never mention internal assessment,"
                "category, priority or triage. Keep replies concise"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Internal assessment: {triage}\n Customer: {input}")
        ])

        ticket_for_triage = RunnableLambda(
            lambda payload : {"ticket_text" : payload["input"]}
        ) | self._triage_chain

        return (RunnablePassthrough.assign(triage=ticket_for_triage)
                | RunnablePassthrough.assign(triage= lambda payload: payload["triage"].as_prompt_text())
                | prompt
                | self._llm
                |StrOutputParser()
                )

    def answer(self, message:str, session_id: str) -> str:
        message = message.strip()
        if not message:
            return "Please enter your question or issue."

        reply = self._reply_chain.invoke({
            "input": message,
            "chat_history": self._memory.history(session_id)
        })
        self._memory.add_turn(session_id, message,reply)
        return reply

    def clear_session(self, session_id: str) -> None:
        self._memory.clear(session_id)

