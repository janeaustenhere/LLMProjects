from __future__ import annotations

from typing import Any
from uuid import uuid4
import httpx

class ShopApiError(RuntimeError):
    """Base error raised for shop API failures."""

class AuthenticationError(ShopApiError):
    """Raised when authentication fails."""

class NotAuthenticatedError(ShopApiError):
    """Raised when shop api fails to authenticate."""


class ShopApiClient:

    def __init__(self, url: str, timeout_seconds: float = 30.0) -> None:
        self._access_token: str | None = None
        self._client = httpx.Client(
            base_url=url.rstrip("/"),
            timeout=timeout_seconds,
            headers={"Accept": "application/json"},
        )

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    def sign_in(self, email: str) -> None:
        normalize_email = email.strip().lower()

        if not normalize_email:
            raise AuthenticationError("Email address is required.")

        try:
            response = self._client.post(
                "/auth/login",
                json={"email": normalize_email},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as e:
            raise AuthenticationError(
                "Authentication failed. Please check your email and try again."
            ) from e

        token = payload.get("access_token")
        if not token:
            raise AuthenticationError("Authentication failed. Please check your email and try again.")
        self._access_token = str(token)

    def sign_out(self) -> None:
            self._access_token = None

    def get_cart(self) -> dict[str, Any]:
            return self._request(
                "GET", "/cart"
            )

    def get_orders(self,
                       order_id: str | None = None) -> dict[str, Any]:

            path = "/orders" if order_id is None else f"/orders/{order_id}"
            return self._request("GET", path)

    def cancel_item(self,
                        order_id: str,
                        item_id: str,
                        quantity: int) -> dict[str, Any]:
            if not 1 <= quantity <= 99:
                raise ValueError("Quantity must be between 1 and 99.")

            return self._request("POST",
                                 f"/orders/{order_id}/items/{item_id}/cancel",
                                 json={"operation_id": str(uuid4()),
                                       "quantity": quantity
                                    },
            )

    def close(self) -> None:
            self._client.close()

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:

            if not self._access_token:
                raise AuthenticationError("Authentication failed. Please check your email and try again.")

            headers = {
                "Authorization": f"Bearer {self._access_token}",
            }

            try:
                response = self._client.request(
                    method,path, headers=headers,
                    **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code

                try:
                    detail = e.response.json()
                except ValueError:
                    detail = e.response.text

                raise ShopApiError(
                    f"Shop api error: {status_code}. Detail: {detail}") from e

            except httpx.HTTPError as e:
                raise ShopApiError(" Shop api error. Couldn't reach server") from e

            except ValueError as e:
                raise ShopApiError(" Shop api return invalid response.") from e