from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from watchfiles import awatch

from src.app.services.csv_parser import CSVCaseParser
from src.app.api.depedencies import get_evaluation_service, get_benchmark_service
from src.app.core.config import get_settings
from src.app.domain.models import BatchEvaluationResponse,FailedEvaluation, BenchmarkResponse
from src.app.services.return_evaluator import ReturnEvaluatorService
from src.app.services.benchmark_service import BenchmarkService

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

@router.post("/benchmark", response_model=BenchmarkResponse)
async def benchmark_router(
        file: UploadFile = File(...),
        service: BenchmarkService = Depends(get_benchmark_service)) -> BenchmarkResponse:

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
        parsed_cases, validation_errors = parser.parse_labeled(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not parsed_cases:
        raise HTTPException(status_code=422, detail="No content provided")

    return await service.evaluate(parsed_cases = parsed_cases,
                                  validation_errors = validation_errors,)

