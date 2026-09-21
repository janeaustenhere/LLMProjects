EXIT_WORDS = {"exit", "quit", "end","stop","bye"}

def run_chat(chat) -> None:
    print("Hopscotch Return Assistant. Type 'exit' to quit")
    while True:
        user_input = input("you: ").strip()

        if not user_input:
            continue
        if user_input.lower() in EXIT_WORDS:
            print("Thank you for using Hopscotch Return Assistant")
            return
        print(f"Assistant: {chat.reply(user_input)}")
