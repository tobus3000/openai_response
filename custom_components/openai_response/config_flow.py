from copy import deepcopy
import logging
from typing import Any, Dict, Optional
from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.helpers.selector import selector
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_host(host: str, hass: core.HassJob) -> None:
    pass


class EndpointSelectionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Start of config flow for endpoint selection."""
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self.data['endpoint_type'] = user_input
            _LOGGER.info(f"init - user_input: {user_input}")
            return await self.async_step_openai()

        return self.async_show_menu(
            step_id="endpoint_selection",
            menu_options=["openapi", "other_llm"],
            description_placeholders={
                "model": "Example model",
            }
        )

    async def async_step_openai(self, user_input=None):
        if user_input is not None:
            self.data['openai'] = user_input
            _LOGGER.info(f"openai - user_input: {user_input}")
            return await self.async_step_settings()
        
        data_schema = {
            vol.Required("API Key"): str,
            vol.Optional("Model", default="text-davinci-003"): str
        }

        return self.async_show_form(step_id="openapi", data_schema=vol.Schema(data_schema))

    async def async_step_custom_llm(self, user_input=None):
        if user_input is not None:
            self.data['custom'] = user_input
            _LOGGER.info(f"openai - user_input: {user_input}")
            return await self.async_step_settings()
        
        data_schema = {
            vol.Required("Host", default="localhost"): str,
            vol.Optional("Port", default=1234): cv.port
        }
        data_schema["transport"] = selector(
            {
                "select": {
                    "options": ["http", "https"],
                }
            }
        )
        return self.async_show_form(step_id="custom_llm", data_schema=vol.Schema(data_schema))

    async def async_step_settings(self, user_input=None):
        if user_input is not None:
            self.data['settings'] = user_input
            _LOGGER.info(f"settings - user_input: {user_input}")
            return await self.async_step_save()
        
        data_schema = {
            vol.Required("name"): str,
            vol.Required("persona"): str,
            vol.Required("keep_history", default=False): cv.boolean,
            vol.Optional("temperature", default=0.9): cv.positive_float,
            vol.Optional("max_tokens", default=300): cv.positive_int
        }

        return self.async_show_form(step_id="openapi", data_schema=vol.Schema(data_schema))

    async def async_step_settings(self, user_input=None):
        save_options = {
            "persona": self.data["settings"],
            "keep_history": self.data["settings"],
            "temperature": self.data["settings"],
            "max_tokens": self.data["settings"]
        }
        
        return self.async_create_entry(
            title="OpenAPI Response Sensor",
            data={
                "name": self.data["openai"]
            },
            options={
                "persona": self.data["settings"],
                "keep_history": self.data["settings"],
                "temperature": self.data["settings"],
                "max_tokens": self.data["settings"]
            },
        )