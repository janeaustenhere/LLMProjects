from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from src.config import get_configs

def create_llm(provider: str):
    config = get_configs()
    if provider == "groq":
        if not config.groq_api_key:
            raise ValueError("Groq API key is required")
        return ChatGroq(
            api_key=config.groq_api_key,
            model=config.groq_model,
            temperature=0.7
        )

    if provider == "gemini":
        if not config.google_api_key:
            raise ValueError("Gemini API key is required")
        return ChatGoogleGenerativeAI(
            google_api_key=config.google_api_key,
            model=config.gemini_model,
            temperature=0.7
        )
