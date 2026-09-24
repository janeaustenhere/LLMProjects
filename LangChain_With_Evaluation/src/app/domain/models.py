from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.app.domain.enums import ReturnReason, Route


class ReturnCase(BaseModel):
    customer_message: str
    item: str = Field(min_length=1)
    order_value_inr: float = Field(ge=0)
    days_since_delivery: int = Field(ge=0)

    @field_validator("customer_message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 15:
            raise ValueError(
                "Customer message must be at least 15 characters"
            )

        if len(value) > 1500:
            raise ValueError(
                "Customer message must not exceed 1500 characters"
            )

        return value


class CaseFacts(BaseModel):
    problem: str = Field(
        description=(
            "A short phrase of no more than eight words describing "
            "what went wrong"
        )
    )

    reason: ReturnReason = Field(
        description=(
            "Primary reason for the return. A safety or health concern "
            "must not be used as the reason; classify the underlying "
            "reason as defect or unclear."
        )
    )

    used_or_worn: Literal["yes", "no", "unknown"]

    safety_or_health_concern: Literal["yes", "no"] = Field(
        description=(
            "Yes when the message mentions injury, allergy, skin "
            "reaction, choking, or another child-safety concern."
        )
    )


class RouteDecision(BaseModel):
    reason: str
    route: Route
    confidence: float = Field(ge=0.0, le=1.0)


class EvaluationResult(BaseModel):
    row_number: int | None = None
    customer_message: str
    route: Route
    confidence: float
    reason: str
    reply: str


class FailedEvaluation(BaseModel):
    row_number: int
    error: str


class BatchEvaluationResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: list[EvaluationResult]
    errors: list[FailedEvaluation]