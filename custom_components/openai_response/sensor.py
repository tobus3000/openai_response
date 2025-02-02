"""
OpenAI Response - Sensor
"""
import logging
from collections.abc import Callable
from dataclasses import dataclass
# from openai import OpenAI
from datetime import datetime
# import voluptuous as vol
# from homeassistant.config_entries import ConfigEntry
# from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_IDLE, STATE_BUFFERING, STATE_OK, STATE_PROBLEM
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo
)
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.dispatcher import async_dispatcher_connect
# import homeassistant.helpers.config_validation as cv
# from homeassistant.core import callback
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import (
    # PLATFORM_SCHEMA,
    # SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    # Entity
)
# from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from .entities import OpenAIResponse
from .const import (
    DOMAIN,
    SIGNAL_EVENTS_CHANGED,
    # DEFAULT_API_KEY
    # CONF_MODEL,
    # CONF_PERSONA,
    # CONF_KEEPHISTORY,
    # CONF_TEMPERATURE,
    # CONF_MAX_TOKENS,
    # DEFAULT_NAME,
    # DEFAULT_MODEL,
    # DEFAULT_PERSONA,
    # DEFAULT_TEMPERATURE,
    # DEFAULT_KEEP_HISTORY,
    # DEFAULT_MAX_TOKENS
)

_LOGGER = logging.getLogger(__name__)
# DEFAULT_API_KEY = "nokey"
DEFAULT_API_BASE = ""
ENTITY_ID_SENSOR_FORMAT = DOMAIN + ".response_{}"

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         vol.Optional(CONF_API_KEY, default=DEFAULT_API_KEY): cv.string,
#         vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
#         vol.Optional(CONF_URL, default=DEFAULT_API_BASE): cv.string,
#         vol.Optional(CONF_PERSONA, default=DEFAULT_PERSONA): cv.string,
#         vol.Optional(CONF_KEEPHISTORY, default=DEFAULT_KEEP_HISTORY): cv.boolean,
#         vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): cv.positive_float,
#         vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): cv.positive_int,
#         vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
#     }
# )

@dataclass(kw_only=True, frozen=True)
class OpenAIResponseSensorEntityDescription(SensorEntityDescription):
    """Describes a OpenAI Response sensor entity."""

    value_fn: Callable[[OpenAIResponse], StateType | datetime]
    signal: str

SENSOR_TYPES: tuple[OpenAIResponseSensorEntityDescription, ...] = (
    OpenAIResponseSensorEntityDescription(
        key="hassio_openai",
        #device_class=SensorDeviceClass.TIMESTAMP,
        translation_key="hassio_openai_response",
        value_fn=lambda data: data.response_text,
        signal=SIGNAL_EVENTS_CHANGED,
    ),
)

def generate_openai_response_sync(
        client,
        model,
        prompt,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty
    ):
    """Setup and return the chat completion."""
    return client.chat.completions.create(
        model=model,
        messages=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

class OpenAIResponseSensor(SensorEntity):
    """Defines the OpenAI Response Sensor object."""
    entity_description: OpenAIResponseSensorEntityDescription

    #def __init__(self, **kwargs):
    def __init__(
        self,
        hass,
        # openai_response: OpenAIResponse,
        entity_description: OpenAIResponseSensorEntityDescription,
        entry_id: str,
        **kwargs
    ) -> None:
        _LOGGER.debug(kwargs)
        self.entity_description = entity_description
        self.entity_id = ENTITY_ID_SENSOR_FORMAT.format(entity_description.key)
        self._attr_unique_id = f"{entry_id}-{entity_description.key}"

        self._attr_device_info = DeviceInfo(
            name="OpenAI Response Sensor",
            identifiers={(DOMAIN, entry_id)},
            entry_type=DeviceEntryType.SERVICE,
        )

        self._hass = hass
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
    def response_text(self) -> str:
        """The response_text of the entity."""
        return self._response_text

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    # @property
    # def state(self) -> str | None:
    #     """The entity state."""
    #     return self._state

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
            self._state = STATE_BUFFERING
            prompt = {"role": "user", "content": new_text}
            # Wipe history if keep_history is False.
            if not self._keep_history:
                self.clear_history()
            self._history.append(prompt)
            response = await self._hass.async_add_executor_job(
                generate_openai_response_sync,
                self._client,
                self._model,
                self._history,
                self._temperature,
                self._max_tokens,
                1,
                0,
                0
            )
            try:
                self._response_text = response.choices[0].message.content
            except Exception:
                self._state = STATE_PROBLEM
            finally:
                self._state = STATE_OK

            _LOGGER.info(self._response_text)
            self.async_write_ha_state()
            if self._keep_history:
                self._history.append({"role": "assistant", "content": self._response_text})
            self._state = STATE_IDLE

    async def async_added_to_hass(self):
        """Listen for state change of `input_text.gpt_input` entity."""
        await super().async_added_to_hass()
        async_track_state_change(
            self._hass, "input_text.gpt_input", self.async_generate_openai_response
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self._hass,
                self.entity_description.signal,
                self.async_write_ha_state,
            )
        )

    async def async_update(self):
        """Currently unused..."""
