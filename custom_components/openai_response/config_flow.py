"""
OpenAI Response - Config/Option Flow
"""
import logging
from typing import Any, Dict, Optional
from openai import OpenAI
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from .sensor import OpenAIResponseSensor, SENSOR_TYPES
from .entities import OpenAIResponseTextInput, OpenAIResponse
from .const import (
    DOMAIN,
    CONF_ENDPOINT_TYPE,
    CONF_MODEL,
    CONF_PERSONA,
    CONF_KEEPHISTORY,
    CONF_TEMPERATURE,
    CONF_MAX_TOKENS,
    DEFAULT_NAME,
    DEFAULT_MODEL,
    DEFAULT_PERSONA,
    DEFAULT_TEMPERATURE,
    DEFAULT_KEEP_HISTORY,
    DEFAULT_MAX_TOKENS
)
from .validators import validate_openai_auth, validate_custom_llm

_LOGGER = logging.getLogger(__name__)

OPENAI_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string
    }
)

CUSTOM_LLM_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_URL): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string
    }
)

class OpenAIResponseCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """OpenAI Response custom config flow."""
    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: Dict[str, str] = {}
        data_schema = {}
        data_schema["endpoint_type"] = selector({
            "select": {
                "options": ["openai", "custom"],
            }
        })
        if user_input is not None:
            self.user_info = user_input
            _LOGGER.info(self.user_info)

            if self.user_info.get(CONF_ENDPOINT_TYPE) == "openai":
                return await self.async_step_setup()
            elif self.user_info.get(CONF_ENDPOINT_TYPE) == "custom":
                return await self.async_step_setup()

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_setup(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in setup process where user configures API key or URL."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_API_KEY):
                try:
                    await validate_openai_auth(user_input[CONF_API_KEY])
                except ValueError:
                    errors["base"] = "openai_auth"
            elif user_input.get(CONF_URL):
                try:
                    await validate_custom_llm(user_input[CONF_URL])
                except ValueError:
                    errors["base"] = "custom_llm_auth"

            if not errors:
                cfg_data = self.user_info
                cfg_data.update(user_input)
                await self._async_add_entities(cfg_data)
                return self.async_create_entry(title="OpenAI Response", data=cfg_data)

        if self.user_info[CONF_ENDPOINT_TYPE] == "openai":
            return self.async_show_form(
                step_id="setup", data_schema=OPENAI_SCHEMA, errors=errors
            )
        elif self.user_info[CONF_ENDPOINT_TYPE] == "custom":
            return self.async_show_form(
                step_id="setup", data_schema=CUSTOM_LLM_SCHEMA, errors=errors
            )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    @callback
    async def _async_add_entities(self, config_entry):
        """Create entities based on user input."""
        _LOGGER.debug("OpenAI Config Entry: %s", config_entry)
        # openai_response: OpenAIResponse = self.hass.data[DOMAIN]
        if config_entry['data'].get('endpoint_type') == "custom":
            client = OpenAI(
                base_url=config_entry['data'].get("url"),
                api_key="nokey"
            )
        else:
            client = OpenAI(
                base_url=config_entry['data'].get("url"),
                api_key=config_entry['data'].get("api_key")
            )
        sensor_config = {
            "name": config_entry['data'].get("name"),
            "client": client,
            "model": config_entry['data'].get("model"),
            "persona": config_entry['options'].get("persona", DEFAULT_PERSONA),
            "temperature": config_entry['options'].get("temperature", DEFAULT_TEMPERATURE),
            "max_tokens": config_entry['options'].get("max_tokens", DEFAULT_MAX_TOKENS)
        }
        entity_list = [
                OpenAIResponseSensor(
                    self.hass,
                    # openai_response,
                    description,
                    config_entry.entry_id,
                    **sensor_config
                ) for description in SENSOR_TYPES
        ]
        unique_name = f"OpenAI Response Input {config_entry.entry_id}"
        input_text_config = {
            "name": unique_name,
            "state": "",
            "icon": "mdi:keyboard"
        }
        entity_list.append(OpenAIResponseTextInput(input_text_config))
        self.hass.async_add_job(self.hass.data[DOMAIN].async_add_entities, [entity_list])
        # async_add_entities(entity_list)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}

        # Retrieve the options associated with the config entry
        options = self.config_entry.options or {}
        if user_input is not None:
            _LOGGER.info(str(user_input))

            if not errors:
                # Value of data will be set on the options property of our config_entry
                # instance.
                _LOGGER.debug("Saving OpenAI Response Sensor options: %s", user_input)
                return self.async_create_entry(
                    title="OpenAI Response Sensor Options",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PERSONA,
                        default=options.get("persona", DEFAULT_PERSONA)
                    ): cv.string,
                    vol.Required(
                        CONF_KEEPHISTORY,
                        default=options.get("keep_history", DEFAULT_KEEP_HISTORY)
                    ): cv.boolean,
                    vol.Optional(
                        CONF_TEMPERATURE,
                        default=options.get("temperature", DEFAULT_TEMPERATURE)
                    ): cv.positive_float,
                    vol.Optional(
                        CONF_MAX_TOKENS,
                        default=options.get("max_tokens", DEFAULT_MAX_TOKENS)
                    ): cv.positive_int
                }
            ),
            errors=errors
        )
