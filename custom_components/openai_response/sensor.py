"""
OpenAI Response - Sensor
"""
import logging
from openai import OpenAI
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_NAME
from .const import (
    CONF_MODEL,
    CONF_API_BASE,
    CONF_PERSONA,
    CONF_KEEPHISTORY,
    CONF_TEMPERATURE,
    CONF_MAX_TOKENS
)
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "hassio_openai_response"
DEFAULT_MODEL = "text-davinci-003"
DEFAULT_KEEP_HISTORY = False
DEFAULT_TEMPERATURE = 0.9
DEFAULT_MAX_TOKENS = 300

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_API_BASE): cv.string,
        vol.Optional(CONF_PERSONA): cv.string,
        vol.Optional(CONF_KEEPHISTORY, default=DEFAULT_KEEP_HISTORY): cv.boolean,
        vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): cv.positive_float,
        vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): cv.positive_int,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup basic OpenAI session."""
    api_base = config.get(CONF_API_BASE)
    api_key = config[CONF_API_KEY]
    if api_base:
        client = OpenAI(base_url=api_base, api_key=api_key)
    else:
        client = OpenAI()

    sensor_config = {
        "hass": hass,
        "name": config[CONF_NAME],
        "client": client,
        "keep_history": config[CONF_KEEPHISTORY],
        "model": config[CONF_MODEL],
        "persona": config[CONF_PERSONA],
        "temperature": config[CONF_TEMPERATURE],
        "max_tokens": config[CONF_MAX_TOKENS]
    }

    async_add_entities(
        [OpenAIResponseSensor(**sensor_config)],
        True
    )

def generate_openai_response_sync(client, **kwargs):
    """Setup and return the chat completion."""
    return client.chat.completions.create(
        model=kwargs.get("model"),
        messages=kwargs.get("prompt"),
        temperature=kwargs.get("temperature"),
        max_tokens=kwargs.get("max_tokens"),
        top_p=kwargs.get("top_p"),
        frequency_penalty=kwargs.get("frequency_penalty"),
        presence_penalty=kwargs.get("presence_penalty")
    )

class OpenAIResponseSensor(SensorEntity):
    """Defines the OpenAI Response Sensor object."""

    def __init__(self, **kwargs):
        self._hass = kwargs.get("hass")
        self._name = kwargs.get("name")
        self._client = kwargs.get("client")
        self._model = kwargs.get("model")
        self._persona = kwargs.get("persona")
        self._keep_history = kwargs.get("keep_history")
        self._temperature = kwargs.get("temperature")
        self._max_tokens = kwargs.get("max_tokens")
        self._state = None
        self._response_text = ""
        self._available = True
        self._history = [
            {
                "role": "system",
                "content": self._persona
            }
        ]

    @property
    def name(self) -> str:
        """The name of the entity."""
        return self._name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> str | None:
        """The entity state."""
        return self._state

    @property
    def extra_state_attributes(self)  -> dict:
        """Returns the `extra_state_attribute` called `response_text`."""
        return {"response_text": self._response_text}

    def clear_history(self) -> None:
        """Resets the chat history."""
        self._history = [
            {
                "role": "system",
                "content": self._persona
            }
        ]

    async def async_generate_openai_response(self, entity_id, old_state, new_state):
        """The main function that interacts with the OpenAPI server and returns the response."""
        new_text = new_state.state
        if new_text:
            self._state = "waiting_for_response"
            prompt = {"role": "user", "content": new_text}
            # Wipe history if keep_history is False.
            if not self._keep_history:
                self.clear_history()
            self._history.append(prompt)
            response_config = {
                "model": self._model,
                "prompt": self._history,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            response = await self._hass.async_add_executor_job(
                generate_openai_response_sync,
                self._client,
                **response_config
            )
            self._response_text = response.choices[0].message.content
            _LOGGER.info(self._response_text)
            self._state = "response_received"
            self.async_write_ha_state()
            if self._keep_history:
                self._history.append({"role": "assistant", "content": self._response_text})

    async def async_added_to_hass(self):
        """Listen for state change of `input_text.gpt_input` entity."""
        self.async_on_remove(
            self._hass.helpers.event.async_track_state_change(
                "input_text.gpt_input", self.async_generate_openai_response
            )
        )

    async def async_update(self):
        """Currently unused..."""
        pass
