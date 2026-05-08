from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import FUEL_TABS, CONF_FUEL_TYPES
from .coordinator import FuelPriceCoordinator

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FuelPriceCoordinator = entry.runtime_data
    selected_fuels: list[str] = entry.data[CONF_FUEL_TYPES]

    async_add_entities(
        FuelPriceSensor(coordinator, fuel_key, FUEL_TABS[fuel_key][1])
        for fuel_key in selected_fuels
    )


class FuelPriceSensor(CoordinatorEntity[FuelPriceCoordinator], SensorEntity):
    _attr_native_unit_of_measurement = "€/l"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gas-station"

    def __init__(
        self,
        coordinator: FuelPriceCoordinator,
        fuel_key: str,
        fuel_label: str,
    ) -> None:
        super().__init__(coordinator)
        self._fuel_key = fuel_key
        self._fuel_label = fuel_label
        city_cap = coordinator.city.capitalize()
        self._attr_name = f"Fuel Price {city_cap} {fuel_label}"
        self._attr_unique_id = f"fuel_price_{coordinator.city}_{fuel_key}"

    def _get_stations(self) -> list[dict]:
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get(self._fuel_key, [])

    @property
    def native_value(self) -> float | None:
        stations = self._get_stations()
        return stations[0]["price"] if stations else None

    @property
    def extra_state_attributes(self) -> dict:
        stations = self._get_stations()
        if not stations:
            return {}
        return {
            "cheapest_station": stations[0]["station"],
            "cheapest_updated": stations[0]["updated"],
            "city": self.coordinator.city,
            "fuel_type": self._fuel_label,
            "stations": [
                {"station": s["station"], "price": s["price"], "updated": s["updated"]}
                for s in stations
            ],
        }
