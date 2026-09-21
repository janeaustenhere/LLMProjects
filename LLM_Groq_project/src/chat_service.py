from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from src.prompts import SYSTEM_PROMPT

class SupportChat:
    def __init__(self, llm):
        self.llm = llm
        self.history = [SystemMessage(content=SYSTEM_PROMPT)]

    def reply(self, user_input:str) -> str:
        self.history.append(HumanMessage(content=user_input))
        response = self.llm.invoke(self.history)
        self.history.append(AIMessage(content=response.text))
        return response.text
