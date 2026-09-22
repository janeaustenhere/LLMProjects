from uuid import uuid4

import gradio as gr

from .service import SupportService


def create_ui(service: SupportService) -> gr.Blocks:
    """Create the presentation layer; it contains no LLM logic."""

    def respond(message: str, history: list, session_id: str) -> str:
        return service.answer(message, session_id)

    with gr.Blocks(title="Hopscotch Support") as demo:
        session_id = gr.State(str(uuid4()))
        gr.Markdown("# Hopscotch Support\nAsk about orders, returns, delivery, or damaged products.")
        gr.ChatInterface(
            fn=respond,
            additional_inputs=[session_id],
            examples=[
                [
                    "The sole of my son's sneakers peeled off after three wears.",
                    "example-defect-session",
                ],
                [
                    "I wore the jacket outside several times, but it is now too small. Can I return it?",
                    "example-return-session",
                ],
                [
                    "Do you ship to Pune?",
                    "example-delivery-session",
                ],
            ]
        )

    return demo