from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from src.app.services.csv_parser import CSVCaseParser
from src.app.api.depedencies import get_evaluation_service
from src.app.core.config import get_settings
from src.app.domain.models import BatchEvaluationResponse,FailedEvaluation
from src.app.services.return_evaluator import ReturnEvaluatorService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

@router.post("/file", response_model=BatchEvaluationResponse)
async def evaluate_file(file: UploadFile = File(...),
                        service: ReturnEvaluatorService = Depends(get_evaluation_service)) -> BatchEvaluationResponse:
    if not file.filename or not file.filename.lower().endswith((".csv")):
        raise HTTPException(status_code=415, detail="only CSV files are supported")
    content = await file.read()
    settings = get_settings()

    if not content:
        raise HTTPException(status_code=400, detail="No content provided")

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File too large")

    parser = CSVCaseParser()

    try:
        parsed_cases, validation_errors = parser.parse(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    cases = [case for _, case in parsed_cases]
    evaluation_results = await service.evaluate_batch(cases)

    successful = []
    errors = list(validation_errors)

    for (row_number, _) , result in zip(parsed_cases, evaluation_results,strict=True):
        if isinstance(result, Exception):
            errors.append(FailedEvaluation(row_number=row_number,
                                           error=str(result),))
        else:
            result.row_number = row_number
            successful.append(result)

    return BatchEvaluationResponse(
        total=len(successful) + len(errors),
        successful=len(successful),
        failed=len(errors),
        results=successful,
        errors=errors
    )

