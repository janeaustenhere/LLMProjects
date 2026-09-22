"""Gradio presentation layer; it contains no LLM or prompt logic."""

import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage

from src.services import SupportChatService


def create_app() -> gr.Blocks:
    service = SupportChatService()

    def chat(message: str, history: list[dict[str, str]]) -> str:
        messages = [
            HumanMessage(item["content"]) if item["role"] == "user" else AIMessage(item["content"])
            for item in history
        ]
        return service.reply(message, messages)

    def triage(ticket: str) -> tuple[str, str, str, str]:
        if not ticket.strip():
            raise gr.Error("Enter a customer ticket first.")
        result = service.triage(ticket)
        return result.category, result.priority, result.details.model_dump_json(indent=2), result.draft_reply

    with gr.Blocks(title="Hopscotch Support") as app:
        gr.Markdown("# Hopscotch Support Assistant\nChat with support or triage a customer ticket.")
        with gr.Tab("Support chat"):
            gr.ChatInterface(fn=chat, type="messages", examples=[
                "My order #HS10234 has not arrived after 6 days."
            ])
        with gr.Tab("Ticket triage"):
            ticket = gr.Textbox(label="Customer ticket", lines=6)
            run = gr.Button("Triage ticket", variant="primary")
            category = gr.Textbox(label="Category")
            priority = gr.Textbox(label="Priority")
            details = gr.Code(label="Extracted details", language="json")
            reply = gr.Textbox(label="Suggested reply", lines=5)
            run.click(triage, inputs=ticket, outputs=[category, priority, details, reply])
    return app
