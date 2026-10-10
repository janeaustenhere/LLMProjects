from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field

class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    answer: str

class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: str = Field(min_length=1, max_length=320)

class LoginResponse(BaseModel):
    access_token: str
    customer: dict[str, Any]

class ShopGateway(ABC):
    @abstractmethod
    def login(self,email:str) -> dict[str, Any]: ...

    @abstractmethod
    def get_cart(self, token:str) -> dict[str, Any]:...

    @abstractmethod
    def get_orders(self, token:str, order_id:str | None = None) -> dict[str, Any]:...

    @abstractmethod
    def cancel_item(self, token:str, order_id:str,
                    item_id: str, quantity: int) -> dict[str, Any]:...



class ConversationStore(ABC):

    @abstractmethod
    def get(self, conversation_id: str) -> list[BaseMessage]:...

    @abstractmethod
    def append(self, conversation_id: str, messages: list[BaseMessage]) -> None:...

    @abstractmethod
    def clear(self, conversation_id: str) -> None:...

