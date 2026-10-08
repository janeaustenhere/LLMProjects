from __future__ import annotations
from typing import Any
from langchain_core.tools import BaseTool, StructuredTool, ToolException, tool
from shop_assistance.client.shop_api_client import ShopApiClient,ShopApiError

class ShopToolProvider:

    def __init__(self, api_client: ShopApiClient) -> None:
        self._api_client = api_client


    def build_tools(self) -> list[BaseTool]:
        return [
            StructuredTool.from_function(
                func = self._get_cart,
                name = "get_cart",
                description=("""
                Inspect the signed-in customer's current cart. Use for cart
                contents, quantities , and totals. Money values are integer paise ,
                where 100 paise equals INR 1. This too cannot modify cart.
                """),
                handle_tool_error=True
            ),
            StructuredTool.from_function(
                func = self._get_orders,
                name = "get_orders",
                description=("""
                List the signed-in Customer's irders or insoect one
                specific order. Omit order_id to list all orders.
                Use this before cancelling an item to obtain the real
                order_id, item_id and active quantity. Never guess Ids.
                """),
                handle_tool_error=True
            ),
            StructuredTool.from_function(
                func=self._cancel_item,
                name = "cancel_item",
                description=("""
                Cancel a whole-number quantity of an order item.
                Use only after get_orders has established the real
                order_id, item_id and available active quantity. 
                The user must explicitly request the cancellation.
                Do not call again automatically after an error. 
                """),
                handle_tool_error=True
            )
        ]

    def _get_cart(self) -> dict[str, Any]:
        """ Get the authenticated customer's cart"""
        return self._execute(self._api_client.get_cart)

    def _get_orders(self, order_id: str | None = None) -> dict[str, Any]:

        """Get all orders or one order by its real identifiers"""

        return self._execute(
            self._api_client.get_orders,
            order_id=order_id)

    def _cancel_item(self,
                     order_id: str,
                     item_id: str,
                     quantity: int,) -> dict[str, Any]:

        """Cancel a requested quantity of an existing order item"""

        return self._execute(
            self._api_client.cancel_item,
            order_id=order_id,
            item_id=item_id,
            quantity=quantity)

    @staticmethod
    def _execute(function: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return function(**kwargs)
        except (ShopApiError, ValueError) as e:
            raise ToolException(str(e)) from e

