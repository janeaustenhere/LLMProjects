import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

@dataclass(frozen=True)
class Config:
    model: str
    api_key: str
    temperature: float

def load_config() -> Config:
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("OpenRouter API key not set")
    return Config(
        model=os.getenv("OPENAI_MODEL"),
        api_key=api_key,
        temperature=float(os.getenv("OPENROUTER_TEMPERATURE","0.3"))
    )

def create_llm() -> ChatOpenAI:
    config = load_config()
    return ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        temperature=config.temperature
    )

