from huggingface_hub import InferenceClient
from .config import Config

class ChatService:
    def __init__(self) -> None:
        config = Config.from_dotenv()
        self.model_id = config.model_id
        self.client = InferenceClient(provider="auto",
                                      api_key=config.hf_token)

    def reply(self, message:str, history: list[dict]) -> str:
        messages = [
            *history,
            {
                "role" : "user",
                "content": message
            }
        ]

        completion = self.client.chat.completions.create(
            model = self.model_id,
            messages = messages,
            max_tokens=300
        )

        return completion.choices[0].message.content or "I could not generate a response."
