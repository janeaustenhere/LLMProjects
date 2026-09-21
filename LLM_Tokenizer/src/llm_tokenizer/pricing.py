from dataclasses import dataclass

@dataclass(frozen=True)
class ModelPricing:
    input_per_millions:float
    output_per_millions:float
    context_window:float

PRICING: dict[str, ModelPricing] = {
        "GPT-5.5" : ModelPricing(5.00,30.00,400_000),
        "Claude Opus 5" : ModelPricing(5.00,25.00,1_000_000),
        "Claude Sonnet 5" : ModelPricing(2.00,10.00,1_000_000),
        "Claude Haiku 4.5": ModelPricing(1.00, 5.00, 200_000),
        "Gemini 3.1 Pro": ModelPricing(2.00, 12.00, 1_000_000),
        "Llama 4 Scout (hosted)": ModelPricing(0.08, 0.30, 10_000_000),
        "DeepSeek V4 Flash": ModelPricing(0.14, 0.28, 1_000_000),
    }

def cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated requested pricing cost"""
    pricing = PRICING[model]
    return (
        input_tokens * pricing.input_per_millions
        + output_tokens * pricing.output_per_millions
    )/1_000_000

def window(model: str) -> int:
    """Return estimated pricing window size"""
    return PRICING[model].context_window

