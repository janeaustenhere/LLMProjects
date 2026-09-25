from io import BytesIO
import pandas as pd
from pydantic import ValidationError
from src.app.domain.models import FailedEvaluation, ReturnCase, LabeledReturnCase

class CSVCaseParser:
    REQUIRED_COLUMNS = {
        "customer_message",
        "item",
        "order_value_inr",
        "days_since_delivery"
    }

    def parse(self, content: bytes) -> tuple[list[tuple[int,ReturnCase]],list[FailedEvaluation]]:
        dataframe = pd.read_csv(BytesIO(content))

        missing = self.REQUIRED_COLUMNS.difference(dataframe.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
        cases: list[tuple[int,ReturnCase]] = []
        errors: list[FailedEvaluation] = []

        for index, row in dataframe.iterrows():
            row_number = int(index) + 2

            try:
                case = ReturnCase.model_validate(row.to_dict())
                cases.append((row_number,case))
            except ValidationError as exc:
                errors.append(FailedEvaluation(
                    row_number = row_number,
                    error = str(exc),
                ))
        return cases, errors


    def parse_labeled(self, content: bytes) -> tuple[list[tuple[int,LabeledReturnCase]],list[FailedEvaluation]]:
        dataframe = pd.read_csv(BytesIO(content))
        required_columns = self.REQUIRED_COLUMNS | {
            "true_route"
        }

        missing = required_columns.difference(dataframe.columns)

        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
        cases: list[tuple[int,LabeledReturnCase]] = []
        errors: list[FailedEvaluation] = []
        for index, row in dataframe.iterrows():
            row_number = int(index) + 2
            try:
                case = LabeledReturnCase.model_validate(row.to_dict())
                cases.append((row_number,case))
            except ValidationError as exc:
                errors.append(FailedEvaluation(row_number=row_number,
                                               error=str(exc)))

        return cases, errors


