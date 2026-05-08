from __future__ import annotations

import logging
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_MINUTES, FUEL_TABS, TOP_N_STATIONS

_LOGGER = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistantIntegration/1.0)"}


class FuelPriceCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, base_url: str, city: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.city = city.lower()
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

        soup = BeautifulSoup(resp.text, "html.parser")
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
                stations.append({
                    "station": cols[1].get_text(strip=True),
                    "price": price,
                    "updated": cols[3].get_text(strip=True),
                })
                if len(stations) == TOP_N_STATIONS:
                    break
            if stations:
                result[fuel_key] = stations

        if not result:
            raise UpdateFailed(f"No price data found for {self.city}")

        return result
