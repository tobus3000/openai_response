import logging
from openai import OpenAI
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_HOST, CONF_PORT
from .const import CONF_PERSONA, CONF_KEEPHISTORY
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)
CONF_MODEL = "model"
DEFAULT_NAME = "hassio_openai_response"
DEFAULT_MODEL = "text-davinci-003"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT): cv.string,
        vol.Optional(CONF_PERSONA): cv.string,
        vol.Optional(CONF_KEEPHISTORY, default=False): cv.boolean,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    api_base = f"http://{host}:{port}/v1"
    api_key = config[CONF_API_KEY]
    client = OpenAI(base_url=api_base, api_key=api_key)

    sensor_config = {
        "hass": hass,
        "name": config[CONF_NAME],
        "client": client,
        "keep_history": config[CONF_KEEPHISTORY],
        "model": config[CONF_MODEL],
        "persona": config[CONF_PERSONA]
    }

    async_add_entities(
        [OpenAIResponseSensor(**sensor_config)],
        True
    )

def generate_openai_response_sync(client, model, prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty):
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
    def __init__(self, **kwargs):
        self._hass = kwargs.get("hass")
        self._name = kwargs.get("name")
        self._client = kwargs.get("client")
        self._model = kwargs.get("model")
        self._persona = kwargs.get("persona")
        self._keep_history = kwargs.get("keep_history")
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
        return self._name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available
    
    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self)  -> dict:
        return {"response_text": self._response_text}

    def clear_history(self) -> None:
        self._history = [
            {
                "role": "system",
                "content": self._persona
            }
        ]

    async def async_generate_openai_response(self, entity_id, old_state, new_state):
        new_text = new_state.state
        if new_text:
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
                0.9,
                300,
                1,
                0,
                0
            )
            self._response_text = response.choices[0].message.content
            _LOGGER.info(self._response_text)
            self._state = "response_received"
            self.async_write_ha_state()
            if self._keep_history:
                self._history.append({"role": "assistant", "content": self._response_text})

    async def async_added_to_hass(self):
        self.async_on_remove(
            self._hass.helpers.event.async_track_state_change(
                "input_text.gpt_input", self.async_generate_openai_response
            )
        )

    async def async_update(self):
        pass
