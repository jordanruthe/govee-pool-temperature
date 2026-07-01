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
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

DEVICE_LIST_URL = "https://app2.govee.com/bff-app/v1/device/list"
LOGIN_URL = "https://app2.govee.com/account/rest/account/v1/login"

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
        self.username = config_entry.data.get('username')
        self.password = config_entry.data.get('password')
        self.config_entry = config_entry

        self.poll_interval = DEFAULT_SCAN_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def _async_login(self, session):
        """Re-authenticate and update stored token."""
        credentials = {
            "client": "a36febdec8a8c629",
            "key": "",
            "email": self.username,
            "password": self.password,
            "view": 0,
        }
        response = await session.post(LOGIN_URL, headers=HEADERS, json=credentials)
        if response.status != 200:
            raise ConfigEntryAuthFailed("Re-authentication failed: bad status")
        data = await response.json(content_type=None)
        token = data.get('client', {}).get('token')
        refresh_token = data.get('client', {}).get('refreshToken')
        if not token:
            raise ConfigEntryAuthFailed(f"Re-authentication failed: {data}")
        self.token = token
        self.refreshToken = refresh_token
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={**self.config_entry.data, "token": token, "refreshToken": refresh_token},
        )
        _LOGGER.info("Successfully re-authenticated with Govee")

    async def _async_update_data(self):
        _LOGGER.info("Govee Coordinator Updating")
        session = async_get_clientsession(self.hass, False)
        headers = {**HEADERS, "authorization": f"Bearer {self.token}"}
        response = await session.get(DEVICE_LIST_URL, headers=headers)
        if response.status != 200:
            _LOGGER.warning("Error getting data, status: %s", response.status)
            return
        data = await response.json()
        if data.get("status") == 401 or "data" not in data:
            _LOGGER.warning("Token invalid, attempting re-authentication")
            if not self.username or not self.password:
                raise ConfigEntryAuthFailed("Token expired and no credentials stored — please reconfigure the integration")
            await self._async_login(session)
            headers = {**HEADERS, "authorization": f"Bearer {self.token}"}
            response = await session.get(DEVICE_LIST_URL, headers=headers)
            data = await response.json()
            if "data" not in data:
                raise UpdateFailed(f"Re-authentication succeeded but device list still failed: {data}")
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