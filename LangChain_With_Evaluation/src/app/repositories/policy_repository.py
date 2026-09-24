from pathlib import Path
from typing import Protocol

class PolicyRepository(Protocol):
    def get_policy(self) -> str:
        pass


class FilePolicyRepository:
    def __init__(self, path:str)->None:
        self._path = Path(path)
        self._cached_policy: str | None = None

    def get_policy(self) -> str:
        if self._cached_policy is None:
            if not self._path.is_file():
                raise FileNotFoundError(f"File not found at {self._path}")

            self._cached_policy = self._path.read_text(encoding="utf-8").strip()

        return self._cached_policy



