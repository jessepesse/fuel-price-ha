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

from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_BASE_URL,
    CONF_FUEL_TYPES,
    CONF_STATION,
    CONF_SOURCE_TYPE,
    CONF_SCAN_INTERVAL,
    SCAN_INTERVAL_MINUTES,
    FUEL_TABS,
    SOURCE_TYPE_A,
    SOURCE_TYPE_B,
    STATION_CHEAPEST,
)
from .coordinator import detect_source_type, TABLE_CLASS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistantIntegration/1.0)"}

FUEL_OPTIONS = [
    {"value": key, "label": label}
    for key, (_tab_id, label) in FUEL_TABS.items()
]

INTERVAL_OPTIONS = [
    {"value": "5", "label": "5 min"},
    {"value": "10", "label": "10 min"},
    {"value": "15", "label": "15 min"},
    {"value": "30", "label": "30 min"},
    {"value": "60", "label": "60 min"},
]


def _validate_and_fetch(base_url: str, city: str) -> tuple[str, str, str, list[str]]:
    """Returns (base_url, city, source_type, station_names_for_type_b)."""
    base_url = base_url.strip().rstrip("/")
    city = city.strip().lower()

    if not city.replace("-", "").replace("_", "").isalpha():
        raise ValueError("invalid_city")

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("invalid_url")

    resp = requests.get(f"{base_url}/{city}/", headers=HEADERS, timeout=10)
    if resp.status_code == 404:
        raise ValueError("city_not_found")
    resp.raise_for_status()

    html_win = resp.content.decode("windows-1252", errors="replace")
    source_type = detect_source_type(resp.text) or detect_source_type(html_win)

    if source_type is None:
        raise ValueError("city_not_found")

    stations: list[str] = []
    if source_type == SOURCE_TYPE_B:
        soup = BeautifulSoup(html_win, "html.parser")
        table = soup.find("table", class_=TABLE_CLASS)
        if table:
            for row in table.select("tr"):
                cols = row.find_all("td")
                if len(cols) >= 5 and not cols[0].get("class"):
                    name = cols[0].get_text(strip=True)
                    if name:
                        stations.append(name)

    return base_url, city, source_type, stations


class FuelPriceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._base_url: str = ""
        self._city: str = ""
        self._source_type: str = SOURCE_TYPE_A
        self._stations: list[str] = []
        self._station: str = STATION_CHEAPEST

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                base_url, city, source_type, stations = await self.hass.async_add_executor_job(
                    _validate_and_fetch,
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
                self._source_type = source_type
                self._stations = stations
                if source_type == SOURCE_TYPE_B:
                    return await self.async_step_station()
                return await self.async_step_fuel_types()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_CITY): str,
            }),
            errors=errors,
        )

    async def async_step_station(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            self._station = user_input[CONF_STATION]
            return await self.async_step_fuel_types()

        station_options = [{"value": STATION_CHEAPEST, "label": "Cheapest (top 5)"}] + [
            {"value": name, "label": name} for name in self._stations
        ]

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema({
                vol.Required(CONF_STATION, default=STATION_CHEAPEST): SelectSelector(
                    SelectSelectorConfig(
                        options=station_options,
                        multiple=False,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            errors=errors,
        )

    async def async_step_fuel_types(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                station_slug = (
                    self._station.lower().replace(" ", "_")[:40]
                    if self._source_type == SOURCE_TYPE_B
                    else ""
                )
                unique_id = f"fuel_price_{urlparse(self._base_url).netloc}_{self._city}"
                if station_slug:
                    unique_id += f"_{station_slug}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                if self._source_type == SOURCE_TYPE_B and self._station != STATION_CHEAPEST:
                    title = self._station[:50]
                else:
                    title = self._city.capitalize()

                entry_data = {
                    CONF_BASE_URL: self._base_url,
                    CONF_CITY: self._city,
                    CONF_SOURCE_TYPE: self._source_type,
                    CONF_FUEL_TYPES: user_input[CONF_FUEL_TYPES],
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                }
                if self._source_type == SOURCE_TYPE_B:
                    entry_data[CONF_STATION] = self._station
                return self.async_create_entry(
                    title=title,
                    data=entry_data,
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
                vol.Required(CONF_SCAN_INTERVAL, default=str(SCAN_INTERVAL_MINUTES)): SelectSelector(
                    SelectSelectorConfig(
                        options=INTERVAL_OPTIONS,
                        multiple=False,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            errors=errors,
        )
