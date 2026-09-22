"""Small command-line entry point for testing the triage workflow."""

from src.services import SupportChatService


def main() -> None:
    service = SupportChatService()
    session_id = "Customer_101"

    print("Hopscotch Support Bot")
    print("Type 'exit' to close the triage session")

    while True:
        message = input("You: ").strip()

        if message.lower() in {"exit", "quit", "bye"}:
            print("Hopscotch Support Bot :  Thanks for contacting ")
            break
        response = service.reply_v2(
            message=message,
            session_id = session_id
        )

        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
