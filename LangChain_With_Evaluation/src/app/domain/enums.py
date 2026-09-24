from enum import StrEnum


class ReturnReason(StrEnum):
    DEFECT = "defect"
    CHANGE_OF_MIND = "change_of_mind"
    ACCIDENT_OR_MISUSE = "accident_or_misuse"
    UNCLEAR = "unclear"


class Route(StrEnum):
    POLICY_VIOLATION = "policy_violation"
    GENUINE_DEFECT = "genuine_defect"
    HUMAN_REVIEW = "human_review"