from typing import Any
from uuid import uuid4

import httpx

from app.domain import  ShopGateway

class ShopApiError(RuntimeError):
    pass

class HTTPShopGateway(ShopGateway):
    def __init__(self, base_url:str, timeout:float) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any]:
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            detail = response.text[:500] if response is not None else str(e)
            raise ShopApiError(f"Shop API error: {detail}") from e

    def login(self, email: str) -> dict[str, Any]:
        return self._json(self._client.post("/auth/login", json={"email": email }))

    def get_cart(self, token: str) -> dict[str, Any]:
        return self._json(self._client.get("/cart",  headers=self._headers(token)))

    def get_orders(self, token: str, order_id: str| None= None) -> dict[str, Any]:
        path = "/orders" if order_id is None else f"/orders/{order_id}"
        return self._json(self._client.get(path, headers=self._headers(token)))

    def cancel_item(self, token:str, order_id:str,
                    item_id: str, quantity: int) -> dict[str, Any]:
        return self._json(self._client.post(
            f"/orders/{order_id}/items/{item_id}/cancel",
            headers=self._headers(token),
            json={"quantity": quantity, "operation_id": str(uuid4())}
        ))

