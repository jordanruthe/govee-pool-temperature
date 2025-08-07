"""Integration 101 Template integration using DataUpdateCoordinator."""

from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

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

class GoveeCoordinator(DataUpdateCoordinator):
    """My example coordinator."""

    devices = []

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        self.hass = hass
        self.token = config_entry.data['token']
        self.refreshToken = config_entry.data['refreshToken']

        self.poll_interval = DEFAULT_SCAN_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def _async_update_data(self):
        _LOGGER.info("Govee Coordinator Updating")
        HEADERS.update({"authorization": f"Bearer {self.token}"})
        session = async_get_clientsession(self.hass, False)
        response = await session.get(DEVICE_LIST_URL, headers=HEADERS)
        if response.status != 200:
            _LOGGER.warning("Error getting data")
            return
        data = await response.json()
        devices = data["data"]["devices"]
        self.devices = devices

    def get_device_ids(self):
        return [device['deviceId'] for device in self.devices]

    def get_device_by_id(
        self, device_id: int
    ):
        """Return device by device id."""
        # Called by the binary sensors and sensors to get their updated data from self.data
        try:
            return [
                device
                for device in self.devices
                if device['deviceId'] == device_id
            ][0]
        except IndexError:
            return None