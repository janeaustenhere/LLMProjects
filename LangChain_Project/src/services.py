from unicodedata import category

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from src.config import create_llm
from src.models import TicketDetails, TriageResult
from src.prompts import (CATEGORY_PROMPT, DETAILS_PROMPT, PRIORITY_PROMPT, REPLY_PROMPT,
                         SUPPORT_CHAT_PROMPT)
from src.memory import get_session_history

class SupportChatService:
    def __init__(self)-> None:
        self.llm = create_llm()

        self.chat_chain = SUPPORT_CHAT_PROMPT | self.llm | StrOutputParser()
        self.chat_with_history = RunnableWithMessageHistory(
           self.chat_chain,
           get_session_history,
           input_messages_key="input",
           history_messages_key="chat_history"

        )
        self.category_chain = CATEGORY_PROMPT | self.llm | StrOutputParser()
        self.details_chain = (DETAILS_PROMPT | self.llm.with_structured_output(TicketDetails))
        self.priority_chain = PRIORITY_PROMPT | self.llm | StrOutputParser()
        self.reply_chain = REPLY_PROMPT | self.llm | StrOutputParser()

    def reply_v2(self, message: str, history: list[BaseMessage]) -> str:
        return self.chat_with_history.invoke(
            {"input" : message},config = {"configurable" : {"session_id" : session_id}}

        ).content.strip()

    def reply(self, message: str, history: list[BaseMessage]) -> str:
        return self.chat_chain.invoke(
            {
                "input": message,
                "chat_history": history,
            }
        ).strip()

    def triage(self, ticket_text: str) -> TriageResult:
        category = self.category_chain.invoke({
            "ticket_text" : ticket_text
        }).strip()

        if category not in {"policy_violation", "genuine_defect","other"}:
            category = "other"

        details = self.details_chain.invoke({"ticket_text" : ticket_text})

        priority = self.priority_chain.invoke(
            {"category" : category,
             "details" : details
             }).strip()
        if priority not in {"low", "medium", "high", "critical"}:
            priority = "medium"

        draft_reply = self.reply_chain.invoke({
            "category" : category,
            "details" : details,
            "ticket_text" : ticket_text
        })

        return TriageResult(
            category = category,
            priority = priority,
            details = details,
            draft_reply = draft_reply
        )

