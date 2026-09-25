from email import policy
from functools import lru_cache
from langchain_openai import ChatOpenAI
from src.app.chains.return_chain_factory import ReturnChainFactory
from src.app.core.config import get_settings
from src.app.repositories.policy_repository import FilePolicyRepository
from src.app.services.return_evaluator import ReturnEvaluatorService
from src.app.services.benchmark_service import BenchmarkService

@lru_cache
def get_evaluation_service() -> ReturnEvaluatorService:
    settings = get_settings()

    chain = get_chain_factory().create()

    return ReturnEvaluatorService(
        chain = chain,
        max_concurrency=settings.batch_concurrency,
    )

@lru_cache
def get_chain_factory() -> ReturnChainFactory:
    settings = get_settings()

    llm = ChatOpenAI(
        model = settings.openai_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openai_api_base,
        temperature=settings.openrouter_temprature,
    )

    policy_repository = FilePolicyRepository(settings.policy_file)

    return ReturnChainFactory(
        llm = llm,
        policy = policy_repository.get_policy()
    )

@lru_cache
def get_benchmark_service() -> BenchmarkService:
    settings = get_settings()
    router_chain = get_chain_factory().create_router_pipeline()

    return BenchmarkService(
        router_chain = router_chain,
        max_concurrency=settings.batch_concurrency,
    )