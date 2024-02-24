from openai import OpenAI
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_HOST, CONF_PORT
from .const import CONF_PERSONA
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback


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
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    api_key = config[CONF_API_KEY]
    name = config[CONF_NAME]
    model = config[CONF_MODEL]
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    persona = config[CONF_PERSONA]
    api_base = f"http://{host}:{port}/v1"
    client = OpenAI(base_url=api_base, api_key=api_key)
    async_add_entities([OpenAIResponseSensor(hass, name, client, model, persona)], True)

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
    def __init__(self, hass, name, client, model, persona):
        self._hass = hass
        self._name = name
        self._client = client
        self._model = model
        self._persona = persona
        self._state = None
        self._response_text = ""
        self._history = [
            {
                "role": "system",
                "content": self._persona
            }
        ]

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {"response_text": self._response_text}

    async def async_generate_openai_response(self, entity_id, old_state, new_state):
        new_text = new_state.state
        if new_text:
            self._history.append({"role": "user", "content": new_text})
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
            self._response_text = response["choices"][0]["message"]["content"]
            self._history.append({"role": "assistant", "content": self._response_text})
            self._state = "response_received"
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.async_on_remove(
            self._hass.helpers.event.async_track_state_change(
                "input_text.gpt_input", self.async_generate_openai_response
            )
        )

    async def async_update(self):
        pass
