import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Configs:
    groq_api_key: str | None
    google_api_key: str | None
    groq_model: str
    gemini_model: str

def get_configs() -> Configs:
    return Configs(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL"),
        gemini_model=os.getenv("GEMINI_MODEL"),
    )