from functools import lru_cache
from langchain_openai import ChatOpenAI
from src.app.chains.return_chain_factory import ReturnChainFactory
from src.app.core.config import get_settings
from src.app.repositories.policy_repository import FilePolicyRepository
from src.app.services.return_evaluator import ReturnEvaluatorService

@lru_cache
def get_evaluation_service() -> ReturnEvaluatorService:
    settings = get_settings()

    llm = ChatOpenAI(
        model = settings.openai_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openai_api_base,
        temperature=settings.openrouter_temprature,
    )

    policy_repository = FilePolicyRepository(settings.policy_file)
    policy = policy_repository.get_policy()

    chain = ReturnChainFactory(
        llm = llm,
        policy = policy,
    ).create()

    return ReturnEvaluatorService(
        chain = chain,
        max_concurrency=settings.batch_concurrency,
    )