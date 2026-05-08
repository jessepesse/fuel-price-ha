from __future__ import annotations

import logging
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SCAN_INTERVAL_MINUTES,
    FUEL_TABS,
    FUEL_COLUMNS,
    TOP_N_STATIONS,
    SOURCE_TYPE_A,
    SOURCE_TYPE_B,
    CONF_SOURCE_TYPE,
    CONF_STATION,
    STATION_CHEAPEST,
)

_LOGGER = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistantIntegration/1.0)"}


TABLE_CLASS = "e10"


def detect_source_type(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("div", id="fuel-95"):
        return SOURCE_TYPE_A
    if soup.find("table", class_=TABLE_CLASS):
        return SOURCE_TYPE_B
    return None


def fetch_type_a(soup: BeautifulSoup, station_filter: str | None = None) -> dict:
    result: dict[str, list] = {}
    for fuel_key, (tab_id, _label) in FUEL_TABS.items():
        tab = soup.find("div", id=tab_id)
        if not tab:
            continue
        stations = []
        for row in tab.select("tbody tr"):
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            try:
                price = float(cols[2].get_text(strip=True).replace(",", "."))
            except ValueError:
                continue
            name = cols[1].get_text(strip=True)
            if station_filter and station_filter != STATION_CHEAPEST and name != station_filter:
                continue
            stations.append({
                "station": name,
                "price": price,
                "updated": cols[3].get_text(strip=True),
            })
            if not station_filter and len(stations) == TOP_N_STATIONS:
                break
        if stations:
            result[fuel_key] = stations
    return result


def fetch_type_b(html: str, station_filter: str | None = None) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_=TABLE_CLASS)
    if not table:
        return {}

    result: dict[str, list] = {}
    for fuel_key, col_idx in FUEL_COLUMNS.items():
        stations = []
        for row in table.select("tr"):
            cols = row.find_all("td")
            if len(cols) < 5 or cols[0].get("class"):
                continue
            name = cols[0].get_text(strip=True)
            if not name:
                continue
            if station_filter and station_filter != STATION_CHEAPEST and name != station_filter:
                continue
            raw = cols[col_idx].get_text(strip=True).lstrip("*")
            if raw == "-" or not raw:
                continue
            try:
                price = float(raw.replace(",", "."))
            except ValueError:
                continue
            updated = cols[1].get_text(strip=True)
            stations.append({
                "station": name,
                "price": price,
                "updated": updated,
            })
        stations.sort(key=lambda s: s["price"])
        if station_filter == STATION_CHEAPEST:
            stations = stations[:TOP_N_STATIONS]
        if stations:
            result[fuel_key] = stations
    return result


class FuelPriceCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, base_url: str, city: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.city = city.lower()
        self.source_type: str = entry.data.get(CONF_SOURCE_TYPE, SOURCE_TYPE_A)
        self.station_filter: str = entry.data.get(CONF_STATION, STATION_CHEAPEST)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.city}",
            config_entry=entry,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
            always_update=False,
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except requests.RequestException as err:
            raise UpdateFailed(f"Connection error for {self.city}: {err}") from err

    def _fetch(self) -> dict:
        url = f"{self.base_url}/{self.city}/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            raise UpdateFailed(f"City '{self.city}' not found at {self.base_url}")
        resp.raise_for_status()

        if self.source_type == SOURCE_TYPE_B:
            html = resp.content.decode("windows-1252", errors="replace")
            result = fetch_type_b(html, self.station_filter)
        else:
            soup = BeautifulSoup(resp.text, "html.parser")
            result = fetch_type_a(soup, self.station_filter)

        if not result:
            raise UpdateFailed(f"No price data found for {self.city}")

        return result
