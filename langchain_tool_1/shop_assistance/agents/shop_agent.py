from __future__ import annotations
import json
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain.agents import create_agent
from langchain_openai import  ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from shop_assistance.agents.prompts.prompts import SHOP_ASSISTANT_SYSTEM_PROMPT
from shop_assistance.domain.models import AgentReply,ToolActivity
from shop_assistance.tools.shop_tool_provider import  ShopToolProvider

class ShopAgent:

    def __init__(
            self,
            model_name: str,
            api_key: str,
            base_url: str,
            tool_provider: ShopToolProvider,
            recursion_limit: int = 20,
    ) -> None:
        model = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        )

        self._recursion_limit = recursion_limit
        self._agent = create_agent(
            model = model,
            tools = tool_provider.build_tools(),
            system_prompt=SHOP_ASSISTANT_SYSTEM_PROMPT,
            checkpointer=InMemorySaver(),
            name="shop_assistance",
        )

    def chat(self, message : str, thread_id: str) -> AgentReply:
            if not message.strip():
                raise ValueError("Message cannot be empty")

            result = self._agent.invoke(
            {
                    "messages": [
                        {
                            "role": "user",
                            "content": message.strip(),
                        }
                    ]
            },
            config={
                    "configurable": {
                        "thread_id": thread_id
                    },
                    "recursion_limit": self._recursion_limit,
                }
            )

            messages = result["messages"]
            current_turn = self._current_turn_messages(messages)

            tool_activities = [
                ToolActivity(
                    tool_name=message.name or "unknown_tool",
                    output=self._decode_tool_output(message.content),
                )

                for message in current_turn
                if isinstance(message, ToolMessage)
            ]

            final_message = next(
                (
                    message
                    for message in reversed(current_turn)
                    if isinstance(message, AIMessage)
                    and not  message.tool_calls
                    and message.content
                ),
                None
            )

            if final_message is None:
                raise  RuntimeError("The agent completed without a final response")

            return AgentReply(
                content=self._content_to_text(final_message.content),
                tool_activities=tool_activities
            )



    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts: list[str] = []

            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(str(block.get("text","")))

            return "\n".join(
                part for part in text_parts if part
            ).strip()

        return str(content)

    @staticmethod
    def _decode_tool_output(content: Any) -> Any:
        if not isinstance(content, str):
            return content

        try:
            return json.loads(content)
        except json.decoder.JSONDecodeError:
            return content


    @staticmethod
    def _current_turn_messages(messages: list[Any]) -> list[Any]:
        for index in range(len(messages)-1, -1, -1):
            if getattr(messages[index], "type", None) == "human":
                return messages[index+1 : ]
        return messages