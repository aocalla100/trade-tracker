import logging
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

WEBULL_HOSTS = {
    "prod": "api.webull.com",
    "sandbox": "us-openapi-alb.uat.webullbroker.com",
}


class WebullService:
    """Wrapper around the Webull OpenAPI Python SDK.

    Reference: webull-openapi-demo-py-us/trade_client_example.py
    """

    def __init__(self):
        from webull.core.client import ApiClient
        from webull.data.data_client import DataClient
        from webull.trade.trade_client import TradeClient

        host = WEBULL_HOSTS.get(settings.webull_environment, WEBULL_HOSTS["sandbox"])
        self._api_client = ApiClient(
            settings.webull_app_key, settings.webull_app_secret, "us"
        )
        self._api_client.add_endpoint("us", host)
        self._data_client = DataClient(self._api_client)
        self._trade_client = TradeClient(self._api_client)

    def get_snapshot(self, symbol: str) -> dict:
        res = self._data_client.market_data.get_snapshot(symbol, "US_STOCK")
        if res.status_code == 200:
            return res.json()
        logger.error("Webull snapshot error: %s %s", res.status_code, res.text)
        return {"error": res.text, "status_code": res.status_code}

    def get_history_bars(
        self, symbol: str, timespan: str = "D1", count: int = 30
    ) -> dict:
        res = self._data_client.market_data.get_history_bar(
            symbol, "US_STOCK", timespan
        )
        if res.status_code == 200:
            return res.json()
        logger.error("Webull bars error: %s %s", res.status_code, res.text)
        return {"error": res.text, "status_code": res.status_code}

    def get_options_chain(
        self, symbol: str, expiration: Optional[str] = None
    ) -> dict:
        res = self._data_client.market_data.get_snapshot(symbol, "US_OPTION")
        if res.status_code == 200:
            return res.json()
        logger.error("Webull options error: %s %s", res.status_code, res.text)
        return {"error": res.text, "status_code": res.status_code}

    def list_accounts(self) -> list[dict[str, Any]]:
        """Return broker accounts (account_id, etc.) for the authenticated app."""
        res = self._trade_client.account_v2.get_account_list()
        if res.status_code != 200:
            logger.error("Webull account list error: %s %s", res.status_code, res.text)
            return []
        data = res.json()
        return data if isinstance(data, list) else []

    def get_account_positions(self, account_id: str) -> list[dict[str, Any]]:
        """Open positions for one account (SDK method is get_account_position)."""
        res = self._trade_client.account_v2.get_account_position(account_id)
        if res.status_code != 200:
            logger.error(
                "Webull positions error: %s %s", res.status_code, res.text
            )
            return []
        data = res.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            items = data.get("items")
            if isinstance(items, list):
                return items
        return []

    def get_account_positions_legacy(self) -> dict:
        """Backward-compatible helper: first account's positions or error dict."""
        accounts = self.list_accounts()
        if not accounts:
            return {"error": "No accounts returned"}
        account_id = accounts[0].get("account_id")
        if not account_id:
            return {"error": "account_id missing"}
        positions = self.get_account_positions(account_id)
        return {"account_id": account_id, "positions": positions}


def get_webull() -> WebullService:
    return WebullService()
