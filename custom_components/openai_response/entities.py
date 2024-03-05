"""
OpenAI Response - Entities
"""
from homeassistant.components.input_text import InputText
from homeassistant.helpers.entity import Entity
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.const import Platform, EVENT_CORE_CONFIG_UPDATE, STATE_OK
from .const import ENTITY_ID

class OpenAIResponse(Entity):
    """Represents the OpenAI Response component."""
    _attr_name = "OpenAI Response"
    entity_id = ENTITY_ID

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the OpenAIResponse."""
        self._hass = hass
        self._config_listener: CALLBACK_TYPE | None = None
        self._update_events_listener: CALLBACK_TYPE | None = None
        self._config_listener = self.hass.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE, self.update_settings
        )
        self.update_settings(initial=True)

    @callback
    def update_settings(self, _: Event | None = None, initial: bool = False) -> None:
        """Update settings."""
        pass

    @callback
    def remove_listeners(self) -> None:
        """Remove listeners."""
        pass
        # if self._config_listener:
        #     self._config_listener()
        # if self._update_events_listener:
        #     self._update_events_listener()
        # if self._update_sun_position_listener:
        #     self._update_sun_position_listener()

    @property
    def state(self) -> str:
        """Return state of the component."""
        return "Active"

class OpenAIResponseTextInput(InputText):
    """Representation of a custom text input entity."""

    def __init__(self, name):
        """Initialize the text input entity."""
        self._name = name
        self._state = None

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def state(self):
        """Return the current state of the entity."""
        return self._state

    async def async_set_text(self, text):
        """Set the text value."""
        self._state = text

    async def async_clear_text(self):
        """Clear the text value."""
        self._state = None
