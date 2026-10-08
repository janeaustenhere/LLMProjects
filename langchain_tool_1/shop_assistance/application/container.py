from __future__ import annotations

from dataclasses import dataclass

from shop_assistance.agents.shop_agent import ShopAgent
from shop_assistance.config.config import Settings
from shop_assistance.client.shop_api_client import ShopApiClient
from shop_assistance.tools.shop_tool_provider import ShopToolProvider


@dataclass
class ApplicationContainer:

    api_client: ShopApiClient
    agent: ShopAgent

    @classmethod
    def build(cls, settings: Settings) -> "ApplicationContainer":
        api_client = ShopApiClient(
            url=settings.shop_api_url,
            timeout_seconds=settings.shop_api_timeout_seconds,
        )

        tool_provider = ShopToolProvider(api_client)

        agent = ShopAgent(
            model_name=settings.openapi_model,
            api_key=settings.open_api_key,
            base_url=settings.openrouter_base_url,
            tool_provider=tool_provider,
            recursion_limit=settings.agent_recursion_limit,
        )

        return cls(
            api_client=api_client,
            agent=agent,
        )