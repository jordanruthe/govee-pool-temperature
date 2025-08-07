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
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_SCAN_INTERVAL

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

        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_method=self.async_update_data,
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def async_update_data(self):
        _LOGGER.info("Govee Coordinator Updating")
        HEADERS.update({"authorization": f"Bearer {self.token}"})
        _LOGGER.info("Token: %s" % self.token)
        session = async_get_clientsession(self.hass, False)
        response = await session.get(DEVICE_LIST_URL, headers=HEADERS)
        if response.status != 200:
            _LOGGER.warning("Error getting data")
            return
        data = await response.json()
        _LOGGER.info("Data: %s", data)
        devices = data["data"]["devices"]
        self.devices = devices
        _LOGGER.info("Devices: %s", self.devices)

        # try:
        #     if not self.api.connected:
        #         await self.hass.async_add_executor_job(self.api.connect)
        #     devices = await self.hass.async_add_executor_job(self.api.get_devices)
        # except APIAuthError as err:
        #     _LOGGER.error(err)
        #     raise UpdateFailed(err) from err
        # except Exception as err:
        #     # This will show entities as unavailable by raising UpdateFailed exception
        #     raise UpdateFailed(f"Error communicating with API: {err}") from err

        # # What is returned here is stored in self.data by the DataUpdateCoordinator
        # return ExampleAPIData(self.api.controller_name, devices)

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