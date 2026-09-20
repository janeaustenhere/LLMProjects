import  gradio as gr
from src.llm_chat.chatservice import ChatService

chat_service = ChatService()

demo =  gr.ChatInterface(
    fn = chat_service.reply,
    title="Hugging Face Chatbot",
    description="Ask Question.",
    examples = ["Explain what a Large Language Model is to 10-year-old.",
                "Give me three idea for Python project."]
)

if __name__ == "__main__":
    demo.launch()