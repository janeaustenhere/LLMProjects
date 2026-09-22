import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Configs:
    api_key: str
    model:str
    temperature: float

    @classmethod
    def load(cls) -> "Configs":
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise AttributeError("API key not provided")
        return cls(api_key=api_key,
                   model=os.getenv("OPENROUTER_MODEL"),
                   temperature=float(os.getenv("OPENROUTER_TEMPERATURE","0.2")))
