"""The Govee Pool Temp integration."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import DOMAIN
from .coordinator import GoveeCoordinator
from .sensor import async_setup_entry as async_sensor_setup_entry
from .config_flow import ConfigFlowHandler

_LOGGER = logging.getLogger(__name__)

CONFIG_FLOW: Final[ConfigFlowHandler] = ConfigFlowHandler()
PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Govee Pool Temp component."""
    _LOGGER.debug("Setting up %s", DOMAIN)
    return True

# async def async_migrate_entry(
#     hass: HomeAssistant, config_entry: ConfigEntry
# ) -> ConfigEntries | None:
#     """Migrate old config entries."""
#     if config_entry.version == 1:
#         config_entry.version = 2
#         await hass.config_entries.async_reload(config_entry.entry_id)
#     return None

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Set up the Govee Pool Temp platform."""
    _LOGGER.info("Setting up %s platform", DOMAIN)
    _LOGGER.info("ConfigEntry: %s", config_entry)

    coordinator = GoveeCoordinator(hass, config_entry)
    config_entry.coordinator = coordinator
    hass.data[DOMAIN] = hass.data.get(DOMAIN, {})
    
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True