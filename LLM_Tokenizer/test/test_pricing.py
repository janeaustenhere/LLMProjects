from src.llm_tokenizer.pricing import cost, window


def test_cost_calculation():
    assert cost("Claude Sonnet 5", 1_000_000, 1_000_000) == 12.0


def test_window():
    assert window("Claude Haiku 4.5") == 200_000