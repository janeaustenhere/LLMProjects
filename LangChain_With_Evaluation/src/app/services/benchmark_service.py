from collections import defaultdict
from typing import Any

from langchain_core.runnables import Runnable

from src.app.domain.enums import Route
from src.app.domain.models import (
BenchmarkResponse, EvaluationScore,FailedEvaluation,LabeledReturnCase,RoutePrediction, ThresholdScore
)

class BenchmarkService:
    """
    Evaluate router predictions against labeled expected routes.
    This service is the modular replacement for predict_all(),
    summarise(), apply_threshold(), the confusion matrix, and the
    threshold sweep from the prototype script.
    """

    DEFAULT_THRESHOLDS = [
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        0.95
    ]


    def __init__(self,router_chain: Runnable, max_concurrency: int = 3) -> None:
        self._router_chain = router_chain
        self._max_concurrency = max_concurrency

    async def evaluate(self, parsed_cases:
                       list[tuple[int,LabeledReturnCase]],
                       validation_errors: list[FailedEvaluation] | None = None,) -> BenchmarkResponse:

        validation_errors = list(validation_errors or [])

        predictions = await self._predict_all(parsed_cases)

        baseline = self._summarise(name="Router alone",
                                   predictions=predictions)

        confusion_matrix = self._create_confusion_matrix(predictions)

        threshold_sweep = self._create_threshold_sweep(predictions)

        return BenchmarkResponse(
            total=len(parsed_cases) + len(validation_errors),
            baseline=baseline,
            confusion_matrix=confusion_matrix,
            predictions=predictions,
            threshold_sweep=threshold_sweep,
            validation_errors=validation_errors
        )


    async def _predict_all(self, parsed_cases:list[tuple[int,LabeledReturnCase]]) -> list[RoutePrediction]:
        """
        RUn the router for every valid labeled case
        :param parsed_cases:
        :return:
        """

        chain_inputs = [
            case.model_dump(exclude={"request_id", "true_route"}) for _,case in parsed_cases
        ]

        raw_results = await self._router_chain.abatch(
            chain_inputs,
            config={
                "max_concurrency": self._max_concurrency,
            },
            return_exceptions= True
        )

        predictions: list[RoutePrediction] = []

        for (row_number, case) , result in zip(parsed_cases,
                                               raw_results,
                                               strict = True):

            if isinstance(result, Exception):
                predictions.append(
                    RoutePrediction(row_number = row_number,
                                    true_route = case.true_route,
                                    predicted_route= "route_error",
                                    confidence=None,
                                    reason = str(result)
                                    )
                )
                continue

            predictions.append(
                    RoutePrediction(row_number = row_number,
                                    request_id=case.request_id,
                                    true_route = case.true_route,
                                    predicted_route= str(result["route"]),
                                    confidence=result["confidence"],
                                    reason=result["reason"],)
                )
            return predictions

    @staticmethod
    def _summarise(name: str,
                   predictions: list[RoutePrediction],) -> EvaluationScore:

        if not predictions:
            return EvaluationScore(
                system=name,
                accuracy=0,
                safety_misses=0,
                wrongful_denials=0,
                wrongful_approvals=0,
                over_escalations=0
            )

        pairs = [
            (
                prediction.true_route.value,
                prediction.predicted_route,
            ) for prediction in predictions
        ]

        total = len(pairs)

        return  EvaluationScore(
            system=name,
            accuracy=round(
                sum(
                    true_route == prediction_route
                    for true_route, prediction_route in pairs
                )/ total, 2
            ),
            safety_misses=sum(
                true_route == Route.HUMAN_REVIEW.value
                and prediction_route != Route.HUMAN_REVIEW.value
                for true_route, prediction_route in pairs
            ),

            wrongful_denials = sum(
                true_route == Route.GENUINE_DEFECT.value
                and prediction_route == Route.POLICY_VIOLATION.value
                for true_route, prediction_route in pairs
            ),

            wrongful_approvals=sum(
                true_route == Route.POLICY_VIOLATION.value
                and prediction_route == Route.GENUINE_DEFECT.value
                for true_route, prediction_route in pairs
            ),

            over_escalations=sum(
                true_route != Route.HUMAN_REVIEW.value
                and prediction_route == Route.HUMAN_REVIEW.value
                for true_route, prediction_route in pairs
            )
        )
    @staticmethod
    def apply_threshold(
            predictions: list[RoutePrediction],
            threshold: float,
    ) -> list[RoutePrediction]:

        adjusted : list[RoutePrediction] = []

        for prediction in predictions:
            should_escalate = (
                    prediction.confidence is None
                    or prediction.confidence < threshold
            )

            if should_escalate:
                adjusted.append(
                    prediction.model_copy(
                        update={
                            "predicted_route" : (Route.HUMAN_REVIEW.value),
                            "reason" : (
                            "Escalated because confidence"
                            f"{prediction.confidence} is below "
                            f"{threshold}"
                        ),
                    }
                )
            )
            else:
                adjusted.append(prediction)
        return adjusted

    def _create_threshold_sweep(self,
                                preditions: list[RoutePrediction],) -> list[RoutePrediction]:

        sweep : list[RoutePrediction] = []

        for threshold in self.DEFAULT_THRESHOLDS:
            adjusted = self.apply_threshold(
                preditions,
                threshold
            )

            score = self._summarise(
                name = f" Threshold {threshold}",
                predictions = adjusted,
            )

            sweep.append(ThresholdScore(
                **score.model_dump(),
                threshold = threshold,
                escalated_total=sum(
                    prediction.predicted_route == Route.HUMAN_REVIEW.value
                    for prediction in adjusted
                ),
            )
        )
        return sweep

    @staticmethod
    def _create_confusion_matrix(
            predictions: list[RoutePrediction],
    ) -> dict[str, dict[str, int]]:
        matrix: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda : defaultdict(int))

        for prediction in predictions:
            matrix[prediction.true_route.value][prediction.predicted_route] += 1

        return {
            true_route: dict(predicted_counts) for true_route, predicted_counts in matrix.items()
        }



