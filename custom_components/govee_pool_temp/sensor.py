import json
import requests
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback, HomeAssistant
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_LIST_URL = "https://app2.govee.com/bff-app/v1/device/list"

HEADERS = {
    "sysversion": "14",
    "country": "US",
    "appversion": "7.0.30",
    "clienttype": "0",
    "timezone": "US/Eastern",
    "accept-language": "en",
    "envid": "0",
    "iotversion": "0",
}

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Govee sensor platform."""

    hass.data[DOMAIN][config_entry.entry_id] = [
        GoveeTemperatureSensor(hass, config_entry, deviceId)
        for deviceId in config_entry.coordinator.get_device_ids()
    ]
    
    async_add_entities(hass.data[DOMAIN][config_entry.entry_id])


class GoveeTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee sensor."""
    _attr_name = "Govee Pool Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, device_id):
        """Initialize the sensor."""
        super().__init__(config_entry.coordinator)
        self._hass = hass
        self.coordinator = config_entry.coordinator
        self._config_entry = config_entry
        self._device = config_entry.coordinator.get_device_by_id(device_id)
        self._device_id = device_id
        self._attr_unique_id = f"{self._device['sku']}_{device_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._device['deviceName']} Temperature"

    @property
    def native_value(self):
        """Return the current temperature."""
        if not self._device["deviceExt"]["lastDeviceData"]:
            return None
        
        data = json.loads(self._device["deviceExt"]["lastDeviceData"])

        temp = float(data["tem"])/100
        return temp
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self._device = self.coordinator.get_device_by_id(self._device_id)
        _LOGGER.info("Device: %s", self._device)
        self.async_write_ha_state()
