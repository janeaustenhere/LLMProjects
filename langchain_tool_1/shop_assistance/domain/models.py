from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ToolActivity:
    tool_name: str
    output: Any

@dataclass(frozen=True)
class AgentReply:
    content: str
    tool_activities: list[ToolActivity] = field(default_factory=list)
