from typing import Literal
from pydantic import BaseModel, Field

class TicketDetails(BaseModel):
    customer_name: str | None = None
    order_id : str | None = None
    product_id: str | None = None
    issue : str = Field(description="One-sentence issue summary.")

class TriageResult(BaseModel):
    category: Literal["policy_violation", "genuine_defect","other"]
    priority: Literal["low", "medium", "high", "critical"]
    details: TicketDetails
    draft_reply: str