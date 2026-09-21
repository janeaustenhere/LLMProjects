from src.chat_service import SupportChat
from src.cli import run_chat
from src.config import get_configs
from src.providers import create_llm
from dotenv import load_dotenv
import os

load_dotenv()

def main() -> None:
    configs = get_configs()
    llm = create_llm(os.getenv("DEFAULT_PROVIDER"))
    chat = run_chat(SupportChat(llm))

if __name__ == "__main__":
    main()
