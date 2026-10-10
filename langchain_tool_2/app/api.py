from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.agent import ShoppingAgent
from app.domain import ChatRequest, ChatResponse, LoginRequest, LoginResponse, ShopGateway
from app.shop import ShopApiError

router = APIRouter(prefix="/api/v1")
bearer = HTTPBearer()

def get_agent(request: Request) -> ShoppingAgent:
    return request.app.state.agent

def get_shop(request: Request) -> ShopGateway:
    return request.app.state.shop

def get_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    return credentials.credentials

def conversation_id(token: str) -> str:
    return sha256(token.encode('utf-8')).hexdigest()

@router.get("/health")
def health() -> dict[str,str]:
    return {"health": "ok"}

@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, shop: Annotated[ShopGateway, Depends(get_shop)]) -> dict:
    try:
        return shop.login(body.email)
    except ShopApiError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

@router.post("/chat", response_model=ChatResponse)
def chat(
        body: ChatRequest,
        token: Annotated[str, Depends(get_token)],
        agent: Annotated[ShopGateway, Depends(get_agent)]
        ) -> ChatResponse:

    try:
        answer = agent.invoke(body.query, token, conversation_id(token))
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

@router.delete("/chat/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(
        request: Request,
        token: Annotated[str, Depends(get_token)],
    ) -> None:
     request.app.state.history.clear(conversation_id(token))


