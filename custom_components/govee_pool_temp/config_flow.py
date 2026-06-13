"""Config flow for Govee integration."""
import json
import logging

from voluptuous import Required, Schema

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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

CREDENTIALS_TEMPLATE = {
    "client": "{username}",
    "email": "{username}@gmail.com",
    "password": "{password}",
}

USER_SCHEMA = Schema({
    Required("username"): str,
    Required("password"): str,
})

class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Starting async_step_user")

        if not user_input:
            _LOGGER.debug("No user input, showing form")
            return self.async_show_form(
                step_id="user",
                data_schema=USER_SCHEMA,
            )

        credentials = {
            "client": "a36febdec8a8c629",
            "key": "",
            "email": user_input.get('username'),
            "password": user_input.get("password"),
            "view": 0,
        }
        _LOGGER.debug(f"Credentials: {credentials}")

        session = async_get_clientsession(self.hass)
        try:
            async with session.post(LOGIN_URL, headers=HEADERS, json=credentials) as response:
                if response.status != 200:
                    _LOGGER.error("Login request failed")
                    return self.async_show_form(
                        step_id="user",
                        data_schema=USER_SCHEMA,
                        errors={"base": "invalid_auth"},
                    )

                data = await response.json(content_type=None)
                _LOGGER.debug("Response: %s", data)
                token = data.get('client', {}).get('token', None)
                refresh_token = data.get('client', {}).get('refreshToken', None)
                _LOGGER.debug("Response: %s", token)
                if token is None:
                    _LOGGER.error("Login request failed")
                    return self.async_show_form(
                        step_id="user",
                        data_schema=USER_SCHEMA,
                        errors={"base": "invalid_auth"},
                    )
            
            headers = HEADERS.copy()
            headers['authorization'] = "Bearer %s" % token
            response = await session.get("https://app2.govee.com/bi/rest/v1/user-informations", headers=headers)
            if response.status != 200:
                _LOGGER.error("Login request failed")
                return self.async_show_form(
                    step_id="user",
                    data_schema=USER_SCHEMA,
                    errors={"base": "invalid_auth"},
                )
            data = await response.json()
            identity_id = data.get('data', {}).get('identity')

        except Exception as e:
            _LOGGER.exception("Error during login request")
            return self.async_show_form(
                step_id="user",
                data_schema=USER_SCHEMA,
                errors={"base": "invalid_auth"},
            )

        _LOGGER.info(f"Successfully logged in, token: {token}")
        await self.async_set_unique_id(identity_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=f"Govee {identity_id[:4]}...", data={"token": token, "refreshToken": refresh_token, "username": user_input.get("username"), "password": user_input.get("password")})

class ConfigFlow(OptionsFlow):
    """Handle options."""

    async def async_step_init(self) -> FlowResult:
        """Manage the Govee options."""
        if not self._async_current_entries:
            return self.async_abort(reason="no_config_entry")

        _LOGGER.debug("Starting async_step_init")
        return self.async_create_entry(title="", data={})