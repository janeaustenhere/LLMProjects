from pyexpat.errors import messages
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig,RunnableLambda
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.domain import ConversationStore, ShopGateway

SYSTEM_PROMPT = """
You are a helpful Hopscotch shopping assistant. Use tools when customer-specific 
data is required and obey each tool description.
Only perform a mutation when the user explicitly requests it.
Before cancellation, call get_orders, use only returned IDs, and verify active quantity.
Never invent customer data or claim success without a successful tool result.
If the request is ambiguous , ask for the missing information.
Money values returned by tools are paise; present them as INR.
Give one concise final answer.

"""

class OrderArgs(BaseModel):
    order_id: str | None = Field(default = None, description="Real Order Id: omit to list orders")

class CancelArgs(BaseModel):
    order_id: str | None = Field(description="Real order Id returned by get_orders")
    item_id: str | None = Field(description="Real Item Id returned by get_orders")
    quantity: int | None = Field(ge = 1, le = 99)

class ShoppingAgent:
    def __init__(self,
                 llm: ChatOpenAI,
                 shop: ShopGateway,
                 memory: ConversationStore,
                 max_tool_rounds: int) -> None:
        self._llm = llm
        self._shop = shop
        self._memory = memory
        self._max_tool_rounds = max_tool_rounds
        self._prompt = ChatPromptTemplate.from_messages([
            ('system', SYSTEM_PROMPT),
            MessagesPlaceholder('history'), ('human', "{query}")
        ])
        self.chain = RunnableLambda(self._run)

    def _tools(self, token:str) -> list[StructuredTool]:
        def get_cart() -> dict[str, Any]:
            """Read the signed-in Customer's cart, quantities , and totals."""
            return self._shop.get_cart(token)

        def get_orders(order_id: str |  None = None) -> dict[str, Any]:
            """List orders or read one order. Call before cancelling, never guess IDs"""
            return self._shop.get_orders(token, order_id)

        def cancel_item(order_id: str, item_id: str, quantity: int) -> dict[str, Any]:
            """Cancel an explicitly requested quantity after get_orders
            verified IDs and stock"""
            return self._shop.cancel_item(token, order_id, item_id, quantity)

        return [
            StructuredTool.from_function(get_cart, name = "get_cart"),
            StructuredTool.from_function(get_orders, name = "get_orders", args_schema = OrderArgs),
            StructuredTool.from_function(cancel_item, name="cancel_item", args_schema = CancelArgs),
        ]

    def invoke (self, query: str, token: str, conversation_id:str) -> str:
        result = self.chain.invoke(
            {"query": query},
             config = {"configurable": {"token" : token,
                                        "conversation_id" : conversation_id}},
        )
        return str(result.content)

    def _run(self, inputs: dict[str, str], config: RunnableConfig) -> AIMessage:

        configurable = config.get("configurable", {})
        token = str(configurable["token"])
        conversation_id = str(configurable["conversation_id"])
        query = inputs["query"]
        history = self._memory.get(conversation_id)
        messages = self._prompt.invoke(
            {"history": history,
            "query" : query}).to_messages()
        tools = self._tools(token)
        tools_by_name = {tool.name: tool for tool in tools}
        model = self._llm.bind_tools(tools)

        response = model.invoke(messages)

        for _ in range(self._max_tool_rounds):
            if not response.tool_calls:
                break

            messages.append(response)

            for call in response.tool_calls:
                tool = tools_by_name.get(call["name"])

                if tool is None:
                    result: Any = {
                        "error": f"Unknown tool: {call['name']}"
                    }
                else:
                    try:
                        result = tool.invoke(call["args"])
                    except Exception as exc:
                        result = {"error": str(exc)}

                messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=call["id"],
                        name=call["name"],
                    )
                )

            # Invoke only after adding results for every requested tool.
            response = model.invoke(messages)
        else:
            raise RuntimeError("Maximum number of tool rounds reached")
        self._memory.append(conversation_id, [HumanMessage(content=query), response])
        return response









