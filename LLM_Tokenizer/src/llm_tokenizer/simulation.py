from .pricing import cost, window
from .schemas import AnalysisResult, SimulationResult
from .tokenizer import count_tokens


def analyze_text(text: str, model: str, system_prompt: str = "", expected_output_tokens: int = 100) -> AnalysisResult:
    input_tokens = count_tokens(system_prompt) + count_tokens(text)
    total_tokens = input_tokens + expected_output_tokens
    context_window = window(model)
    return AnalysisResult(
        input_tokens=input_tokens,
        output_tokens=expected_output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=cost(model, input_tokens, expected_output_tokens),
        context_window=context_window,
        window_usage_percent=total_tokens / context_window * 100,
        fits_in_context=total_tokens <= context_window,
    )


def simulate_conversation(messages: list[str], model: str, system_prompt: str = "", reply_tokens: int = 100, keep_last_messages: int | None = None) -> SimulationResult:
    history: list[int] = []
    total_cost = 0.0
    peak_input_tokens = 0
    first_over_limit_turn: int | None = None
    context_window = window(model)
    turns_processed = 0

    for turn, message in enumerate(messages, start=1):
        previous_tokens = history if keep_last_messages is None else history[-keep_last_messages:]
        input_tokens = count_tokens(system_prompt) + sum(previous_tokens) + count_tokens(message)
        request_total = input_tokens + reply_tokens
        peak_input_tokens = max(peak_input_tokens, input_tokens)
        turns_processed = turn
        if request_total > context_window:
            first_over_limit_turn = turn
            break
        total_cost += cost(model, input_tokens, reply_tokens)
        history.extend([count_tokens(message), reply_tokens])

    return SimulationResult(
        turns_processed=turns_processed,
        total_cost_usd=total_cost,
        peak_input_tokens=peak_input_tokens,
        context_window=context_window,
        peak_window_usage_percent=(peak_input_tokens + reply_tokens) / context_window * 100,
        first_over_limit_turn=first_over_limit_turn,
    )
