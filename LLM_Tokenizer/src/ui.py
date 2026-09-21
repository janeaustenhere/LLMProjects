import gradio as gr

from llm_tokenizer.pricing import PRICING
from llm_tokenizer.simulation import analyze_text, simulate_conversation
from llm_tokenizer.tokenizer import tokenize


def analyze_request(text, model, system_prompt, output_tokens):
    if not text or not text.strip():
        raise gr.Error("Enter text to analyze.")

    result = analyze_text(
        text=text,
        model=model,
        system_prompt=system_prompt,
        expected_output_tokens=int(output_tokens),
    )

    summary = (
        f"## Estimate\n\n"
        f"- Input tokens: **{result.input_tokens:,}**\n"
        f"- Expected output tokens: **{result.output_tokens:,}**\n"
        f"- Total request tokens: **{result.total_tokens:,}**\n"
        f"- Estimated cost: **${result.estimated_cost_usd:.6f}**\n"
        f"- Context window: **{result.context_window:,}** tokens\n"
        f"- Window usage: **{result.window_usage_percent:.3f}%**\n"
        f"- Fits in context: **{'Yes' if result.fits_in_context else 'No'}**"
    )

    token_preview = " | ".join(tokenize(text)[:100])
    return summary, token_preview


def analyze_conversation(text, model, system_prompt, reply_tokens, keep_last):
    messages = [line.strip() for line in text.splitlines() if line.strip()]

    if not messages:
        raise gr.Error("Enter at least one message, using one line per turn.")

    keep_last_messages = None if keep_last == 0 else int(keep_last)

    result = simulate_conversation(
        messages=messages,
        model=model,
        system_prompt=system_prompt,
        reply_tokens=int(reply_tokens),
        keep_last_messages=keep_last_messages,
    )

    status = (
        f"Over limit on turn **{result.first_over_limit_turn}**."
        if result.first_over_limit_turn
        else "All supplied turns fit in the context window."
    )

    return (
        f"## Conversation estimate\n\n"
        f"- Turns processed: **{result.turns_processed}**\n"
        f"- Total estimated cost: **${result.total_cost_usd:.6f}**\n"
        f"- Peak input tokens: **{result.peak_input_tokens:,}**\n"
        f"- Peak context usage: **{result.peak_window_usage_percent:.3f}%**\n"
        f"- {status}"
    )


with gr.Blocks(title="LLM Token & Cost Calculator") as app:
    gr.Markdown("# LLM Token & Cost Calculator")

    with gr.Tab("Single request"):
        with gr.Row():
            with gr.Column():
                request_text = gr.Textbox(
                    label="User text",
                    lines=10,
                    placeholder="Paste a prompt, ticket, or message here.",
                )
                request_system_prompt = gr.Textbox(
                    label="System prompt (optional)",
                    lines=4,
                )
                request_model = gr.Dropdown(
                    choices=list(PRICING),
                    value="Claude Sonnet 5",
                    label="Model",
                )
                request_output_tokens = gr.Slider(
                    1,
                    10_000,
                    value=100,
                    step=1,
                    label="Expected output tokens",
                )
                request_button = gr.Button("Analyze", variant="primary")

            with gr.Column():
                request_result = gr.Markdown()
                token_preview = gr.Textbox(
                    label="First 100 tokens",
                    lines=8,
                )

        request_button.click(
            analyze_request,
            inputs=[
                request_text,
                request_model,
                request_system_prompt,
                request_output_tokens,
            ],
            outputs=[request_result, token_preview],
        )

    with gr.Tab("Conversation simulation"):
        conversation_text = gr.Textbox(
            label="Conversation messages",
            lines=12,
            placeholder="One user message per line.",
        )
        conversation_system_prompt = gr.Textbox(
            label="System prompt (optional)",
            lines=4,
        )

        with gr.Row():
            conversation_model = gr.Dropdown(
                choices=list(PRICING),
                value="Claude Sonnet 5",
                label="Model",
            )
            reply_tokens = gr.Slider(
                1,
                5_000,
                value=100,
                step=1,
                label="Estimated reply tokens per turn",
            )
            keep_last = gr.Slider(
                0,
                50,
                value=0,
                step=1,
                label="Keep last messages (0 = keep all)",
            )

        conversation_button = gr.Button("Simulate", variant="primary")
        conversation_result = gr.Markdown()

        conversation_button.click(
            analyze_conversation,
            inputs=[
                conversation_text,
                conversation_model,
                conversation_system_prompt,
                reply_tokens,
                keep_last,
            ],
            outputs=conversation_result,
        )

if __name__ == "__main__":
    app.launch()