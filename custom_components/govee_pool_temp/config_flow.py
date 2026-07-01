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


class InvalidAuth(Exception):
    """Raised when Govee login/identity lookup fails."""


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    async def _async_validate_login(self, username: str, password: str) -> dict:
        """Log in to Govee and return token/refreshToken/identity_id.

        Raises InvalidAuth if login or identity lookup fails.
        """
        credentials = {
            "client": "a36febdec8a8c629",
            "key": "",
            "email": username,
            "password": password,
            "view": 0,
        }
        _LOGGER.debug(f"Credentials: {credentials}")

        session = async_get_clientsession(self.hass)
        try:
            async with session.post(LOGIN_URL, headers=HEADERS, json=credentials) as response:
                if response.status != 200:
                    _LOGGER.error("Login request failed")
                    raise InvalidAuth

                data = await response.json(content_type=None)
                _LOGGER.debug("Response: %s", data)
                token = data.get('client', {}).get('token', None)
                refresh_token = data.get('client', {}).get('refreshToken', None)
                _LOGGER.debug("Response: %s", token)
                if token is None:
                    _LOGGER.error("Login request failed")
                    raise InvalidAuth

            headers = HEADERS.copy()
            headers['authorization'] = "Bearer %s" % token
            response = await session.get("https://app2.govee.com/bi/rest/v1/user-informations", headers=headers)
            if response.status != 200:
                _LOGGER.error("Login request failed")
                raise InvalidAuth
            data = await response.json()
            identity_id = data.get('data', {}).get('identity')

        except InvalidAuth:
            raise
        except Exception:
            _LOGGER.exception("Error during login request")
            raise InvalidAuth

        _LOGGER.info(f"Successfully logged in, token: {token}")
        return {
            "token": token,
            "refreshToken": refresh_token,
            "identity_id": identity_id,
        }

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Starting async_step_user")

        if not user_input:
            _LOGGER.debug("No user input, showing form")
            return self.async_show_form(
                step_id="user",
                data_schema=USER_SCHEMA,
            )

        try:
            result = await self._async_validate_login(
                user_input.get("username"), user_input.get("password")
            )
        except InvalidAuth:
            return self.async_show_form(
                step_id="user",
                data_schema=USER_SCHEMA,
                errors={"base": "invalid_auth"},
            )

        identity_id = result["identity_id"]
        await self.async_set_unique_id(identity_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Govee {identity_id[:4]}...",
            data={
                "token": result["token"],
                "refreshToken": result["refreshToken"],
                "username": user_input.get("username"),
                "password": user_input.get("password"),
            },
        )

    async def async_step_reauth(self, entry_data: dict) -> FlowResult:
        """Handle reauthentication triggered by ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        """Confirm reauth by re-collecting username/password."""
        reauth_entry = self._get_reauth_entry()

        if not user_input:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=USER_SCHEMA,
                description_placeholders={"username": reauth_entry.data.get("username", "")},
            )

        try:
            result = await self._async_validate_login(
                user_input.get("username"), user_input.get("password")
            )
        except InvalidAuth:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=USER_SCHEMA,
                errors={"base": "invalid_auth"},
                description_placeholders={"username": reauth_entry.data.get("username", "")},
            )

        return self.async_update_reload_and_abort(
            reauth_entry,
            data={
                **reauth_entry.data,
                "token": result["token"],
                "refreshToken": result["refreshToken"],
                "username": user_input.get("username"),
                "password": user_input.get("password"),
            },
        )


class ConfigFlow(OptionsFlow):
    """Handle options."""

    async def async_step_init(self) -> FlowResult:
        """Manage the Govee options."""
        if not self._async_current_entries:
            return self.async_abort(reason="no_config_entry")

        _LOGGER.debug("Starting async_step_init")
        return self.async_create_entry(title="", data={})
