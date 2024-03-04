from homeassistant.components.input_text import InputText

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the custom component."""
    # Example: Create a text input entity
    async_add_entities([OpenAIResponseTextInput()])

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
