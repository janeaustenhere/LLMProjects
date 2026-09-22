from dataclasses import dataclass

@dataclass(frozen=True)
class TriageResult:

    """Internal ticket assessment, it is never shown to the customer"""

    category: str
    priority: str

    def as_prompt_text(self) -> str:
        return f"category = {self.category}; priority = {self.priority}"
    
