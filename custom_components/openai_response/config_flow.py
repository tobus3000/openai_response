import logging
from typing import Any, Dict, Optional
from openai import OpenAI
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
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

async def validate_openai_auth(api_key: str) -> None:
    """Validates OpenAI auth.

    Raises a ValueError if the API Key is invalid.
    """
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "system", "content": "This is a connection test."}],
            max_tokens=5
        )
    except Exception as exc:
        _LOGGER.error(str(exc))
        raise ValueError from exc

async def validate_custom_llm(base_url: str) -> None:
    """Validates custom LLM connectivity.

    Raises a ValueError if the machine cannot be reached.
    """
    client = OpenAI(base_url=base_url, api_key="nokey")
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "system", "content": "This is a connection test."}],
            max_tokens=5
        )
    except Exception as exc:
        _LOGGER.error(str(exc))
        raise ValueError from exc

class OpenAIResponseCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """OpenAI Response custom config flow."""
    VERSION = 1
    data: Optional[Dict[str, Any]]

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
