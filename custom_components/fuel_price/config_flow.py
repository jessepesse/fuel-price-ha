from __future__ import annotations

import voluptuous as vol
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN, CONF_CITY, CONF_BASE_URL, CONF_FUEL_TYPES, FUEL_TABS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistantIntegration/1.0)"}

FUEL_OPTIONS = [
    {"value": key, "label": label}
    for key, (_tab_id, label) in FUEL_TABS.items()
]


def _validate_connection(base_url: str, city: str) -> tuple[str, str]:
    base_url = base_url.strip().rstrip("/")
    city = city.strip().lower()

    if not city.replace("-", "").isalpha():
        raise ValueError("invalid_city")

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("invalid_url")

    resp = requests.get(f"{base_url}/{city}/", headers=HEADERS, timeout=10)
    if resp.status_code == 404:
        raise ValueError("city_not_found")
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    if not soup.find("div", id="fuel-95"):
        raise ValueError("city_not_found")

    return base_url, city


class FuelPriceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._base_url: str = ""
        self._city: str = ""

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                base_url, city = await self.hass.async_add_executor_job(
                    _validate_connection,
                    user_input[CONF_BASE_URL],
                    user_input[CONF_CITY],
                )
            except ValueError as err:
                errors["base"] = str(err)
            except requests.RequestException:
                errors["base"] = "cannot_connect"
            else:
                self._base_url = base_url
                self._city = city
                return await self.async_step_fuel_types()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_CITY): str,
            }),
            errors=errors,
        )

    async def async_step_fuel_types(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                await self.async_set_unique_id(
                    f"fuel_price_{urlparse(self._base_url).netloc}_{self._city}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=self._city.capitalize(),
                    data={
                        CONF_BASE_URL: self._base_url,
                        CONF_CITY: self._city,
                        CONF_FUEL_TYPES: user_input[CONF_FUEL_TYPES],
                    },
                )

        return self.async_show_form(
            step_id="fuel_types",
            data_schema=vol.Schema({
                vol.Required(CONF_FUEL_TYPES, default=list(FUEL_TABS.keys())): SelectSelector(
                    SelectSelectorConfig(
                        options=FUEL_OPTIONS,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            errors=errors,
        )
