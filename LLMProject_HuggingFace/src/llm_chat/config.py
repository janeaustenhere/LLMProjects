import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
    hf_token: str
    model_id: str

    @classmethod
    def from_dotenv(cls) -> 'Config':
        load_dotenv()

        hf_token = os.getenv("HF_TOKEN")
        model_id = os.getenv("MODEL_ID")

        if not hf_token or not hf_token.startswith("hf_"):
            raise RuntimeError("HF_TOKEN in valid")

        if not model_id:
            raise RuntimeError("MODEL_ID is not valid")

        return cls(hf_token=hf_token,model_id=model_id)


