from langchain_core.runnables import (
    Runnable,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough)

from typing import Any

from langchain_core.output_parsers import (
    PydanticOutputParser,
    StrOutputParser
)
from src.app.chains.prompts import (
    create_routing_prompt,
    create_summary_prompt,
    create_genuine_defect_prompt,
    create_fact_extraction_prompt,
    create_policy_violation_prompt,
    create_human_review_prompt
)
from src.app.domain.models import CaseFacts, ReturnCase, RouteDecision
from langchain_openai import ChatOpenAI


class ReturnChainFactory:
    """
    Construct the complete return-evaluation LangChain pipeline.

    The Factory owns chain construction only. It does not read files,
    initialize application settings, expose API endpoints or execute
    test cases.

    """

    def __init__(self, llm :ChatOpenAI, policy: str) -> None:
        if not policy or not policy.strip():
            raise ValueError("Policy cannot be empty")

        self._llm = llm
        self._policy = policy.strip()

    def create(self) -> Runnable:
        """"
        Build and return the complete runnable LangChain pipeline.
        Input:
            A dictionary matching Return Case.
        Output:
        {
        "customer_message": str,
        brief_text": str,
        "route": str,
        "confidence": float,
        "reason": str,
        "reply":str
        }
        """
        facts_chain = self._create_facts_chain()
        summary_chain = self._create_summary_chain()
        intake_chain = self._create_intake_chain(
            facts_chain = facts_chain,
            summary_chain = summary_chain
        )
        router_chain = self._create_router_chain()
        reply_branch = self._create_reply_branch_chain()

        return (
            RunnableLambda(self._validate_input)
            | intake_chain
            | RunnablePassthrough.assign(decision = router_chain)
            | RunnableLambda(self._flatten_state)
            | RunnablePassthrough.assign(reply = reply_branch)
        )

    def _create_facts_chain(self) -> Runnable:
        prompt = create_fact_extraction_prompt()

        structured_facts_llm = self._llm.with_structured_output(
            CaseFacts,
            method="function_calling",
        )

        return (
                prompt
                | structured_facts_llm
                | RunnableLambda(self._model_to_dict)
        )

    def _create_summary_chain(self) -> Runnable:
        """
        Create the structured summary chain.
        :return:
        """
        return (
            create_summary_prompt()
            | self._llm
            | StrOutputParser()
        )

    def _create_intake_chain(
            self,
            facts_chain: Runnable,
            summary_chain: Runnable,
    ) -> Runnable:
        gather_chain = RunnableParallel(
            facts=facts_chain,
            summary=summary_chain,
            flags=RunnableLambda(self._compute_flags),
            request=RunnablePassthrough(),
        )

        return gather_chain | RunnableLambda(self._build_brief)

    def _create_router_chain(self) -> Runnable:
        """
        Create the structured router chain.
        :return:
        """
        prompt = create_routing_prompt(self._policy)

        structured_router_llm = self._llm.with_structured_output(
            RouteDecision,
            method="function_calling"
        )

        return(
            prompt
            | structured_router_llm
            | RunnableLambda(self._model_to_dict)
        )

    def _create_reply_branch_chain(self) -> Runnable:
        """
        Create the structured reply branch.
        :return:
        """

        policy_violation_chain = (
            create_policy_violation_prompt(self._policy)
            | self._llm
            | StrOutputParser()
        )

        genuine_defect_chain = (
            create_genuine_defect_prompt(self._policy)
            | self._llm
            | StrOutputParser()
        )

        human_review_chain = (
            create_human_review_prompt(self._policy)
            | self._llm
            | StrOutputParser()
        )

        return RunnableBranch(
            (
                self._is_policy_violation,
                policy_violation_chain
            ),
            (
                self._is_genuine_defect,
                genuine_defect_chain
            ),
            human_review_chain
        )

    @staticmethod
    def _validate_input(data: dict[str,Any]) -> dict[str,Any]:
        """
        Validate and normalize pipeline inout using the domain model.
        Pydantic raise ValidationError when required values are missing
        or invalid.

        :param data:
        :return:
        """
        validated_case = ReturnCase.model_validate(data)
        return validated_case.model_dump(mode="json")


    @staticmethod
    def _flatten_state(state: dict[str, Any]) -> dict[str, Any]:
        request = state["request"]
        decision = state["decision"]

        return {
            "customer_message": request["customer_message"],
            "brief_text": state["brief_text"],
            "route": decision["route"],
            "confidence": decision["confidence"],
            "reason": decision["reason"],
        }
    @staticmethod
    def _model_to_dict(value : Any) -> dict[str,Any]:
        """
        Convert a Pydnatic model to a JSON-compatible dictionary.
        The dictionary fallback
        :param value:
        :return:
        """

        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")

        raise TypeError(
            "Expected a Pydantic model or dictionary"
            f"but received {type(value).__name__}"
        )
    @staticmethod
    def _compute_flags(request: dict[str,Any]) -> dict[str,Any]:
        """
        Calculate exact order flags without using an LLM
        :param request:
        :return:
        """

        days_since_delivery = request["days_since_delivery"]
        order_value = request["order_value_inr"]

        return {
            "within_30_days": days_since_delivery <= 30,
            "within_90_days": days_since_delivery <= 90,
            "high_value" : order_value > 5000
        }

    @staticmethod
    def _build_brief(state: dict[str,Any]) -> dict[str,Any]:
        """
        Combine the original request, extracted facts, summary, and
        deterministic flags into a case brief for the router.
        :param state:
        :return:
        """


        request = state["request"]
        facts = state["facts"]
        flags = state["flags"]

        def yes_or_no(value: bool) -> bool:
            return "yes" if value else "no"

        brief_text = (
            "CASE BRIEF \n"
            f"Item : {request['item']} \n"
            f"Order Value: INR : {request['order_value_inr']:,.2f} \n"
            f"Days Since Delivery : {request['days_since_delivery']} \n"
            f"Within 30-day-window: {yes_or_no(flags['within_30_days'])} \n"
            f"within 90-day-window: {yes_or_no(flags['within_90_days'])}\n"
            f"High value, over iNR 5000: {yes_or_no(flags['high_value'])}\n"
            f"Customer reason: {facts['reason']}\n"
            f"Used or Worn: {facts['used_or_worn']}\n"
            f"Safety or Health concern: {facts['safety_or_health_concern']}\n"
            f"Reported problem: {facts['problem']}\n"
            f"Neutral summary:{state['summary']}\n"
            f"Original Customer message: {request['customer_message']}\n"
        )

        return {
            **state,
            "brief_text": brief_text,
        }
    @staticmethod
    def _is_policy_violation(state: dict[str,Any]) -> bool:
        return state["route"] == "policy_violation"

    @staticmethod
    def _is_genuine_defect(state: dict[str,Any]) -> bool:
        return state["route"] == "genuine_defect"

    def create_router_pipeline(self) -> Runnable:
        """
        Create a pipeline that performs intake and routing but does not generate a customer reply.
        This pipeline is used for offline benchmark evaluation
        :return:
        """
        facts_chain = self._create_facts_chain()
        summary_chain = self._create_summary_chain()

        intake_chain = self._create_intake_chain(
            facts_chain=facts_chain,
            summary_chain=summary_chain,
        )

        router_chain = self._create_router_chain()

        return (
            RunnableLambda(self._validate_input)
            | intake_chain
            | RunnablePassthrough.assign(decision = router_chain)
            | RunnableLambda(self._flatten_state))



