from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisResult:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    context_window: int
    window_usage_percent: float
    fits_in_context: bool


@dataclass(frozen=True)
class SimulationResult:
    turns_processed: int
    total_cost_usd: float
    peak_input_tokens: int
    context_window: int
    peak_window_usage_percent: float
    first_over_limit_turn: int | None
