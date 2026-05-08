from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_CITY, CONF_BASE_URL
from .coordinator import FuelPriceCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type FuelPriceConfigEntry = ConfigEntry[FuelPriceCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FuelPriceConfigEntry) -> bool:
    coordinator = FuelPriceCoordinator(hass, entry, entry.data[CONF_BASE_URL], entry.data[CONF_CITY])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FuelPriceConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
