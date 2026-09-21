from src.llm_tokenizer.simulation import analyze_text, simulate_conversation


def test_analysis_counts_output_tokens():
    result = analyze_text(
        text="Hello",
        model="Claude Haiku 4.5",
        expected_output_tokens=50,
    )

    assert result.input_tokens > 0
    assert result.output_tokens == 50
    assert result.total_tokens == result.input_tokens + 50


def test_simulation_detects_context_limit():
    messages = ["hello"] * 5

    result = simulate_conversation(
        messages=messages,
        model="Claude Haiku 4.5",
        reply_tokens=100,
    )

    assert result.turns_processed == 5
    assert result.total_cost_usd > 0