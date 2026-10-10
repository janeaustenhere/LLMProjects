from contextlib import asynccontextmanager
from wsgiref.util import application_uri

from fastapi import  FastAPI
from langchain_openai import ChatOpenAI

from app.agent import ShoppingAgent
from app.api import router
from app.config import get_settings
from app.memory import InMemoryConversationStore
from app.shop import HTTPShopGateway

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    shop = HTTPShopGateway(settings.shop_api_url, settings.shop_api_timeout_seconds)

    memory = InMemoryConversationStore(settings.max_history_message)
    llm = ChatOpenAI(
        model = settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0,
        timeout=settings.llm_timeout_seconds,
        max_retries=1
    )

    app.state.shop = shop
    app.state.memory = memory
    app.state.agent= ShoppingAgent(llm, shop, memory, settings.max_tool_rounds)
    yield
    shop.close()

def create_app() -> FastAPI:
    application = FastAPI(title="Hopscotch Assistant API ",
                          version="1.0.0", lifespan=lifespan)
    application.include_router(router)
    return application

app = create_app()
