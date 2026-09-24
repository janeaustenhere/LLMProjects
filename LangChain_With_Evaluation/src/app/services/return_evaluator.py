from src.app.domain.models import EvaluationResult, ReturnCase

class ReturnEvaluatorService:

    def __init__(self, chain, max_concurrency: int = 3) ->None:
        self._chain = chain
        self._max_concurrency = max_concurrency

    async def evaluate(self, case: ReturnCase) -> EvaluationResult:
        result = await self._chain.ainvoke(case.model_dump())
        return EvaluationResult(**result)

    async def evaluate_batch(self, cases: list[ReturnCase]) -> list[EvaluationResult | Exception]:
        raw_results = await self._chain.abatch(
            [case.model_dump() for case in cases],
            config = {"max_concurrency": self._max_concurrency},
            return_exceptions = True
        )

        return [
            result if isinstance(result, Exception) else
            EvaluationResult(**result) for result in raw_results
        ]

