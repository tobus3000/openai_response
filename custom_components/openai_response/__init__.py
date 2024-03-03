"""OpenAI Response custom component."""
import logging
from homeassistant import config_entries
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.const import Platform, EVENT_CORE_CONFIG_UPDATE
from homeassistant.helpers.entity import Entity
from .const import DOMAIN
from .config_flow import OpenAIResponseCustomConfigFlow
_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]
ENTITY_ID = "openai_response"

async def async_setup(
        hass: HomeAssistant,
        config: dict
    ) -> bool:
    """Set up the OpenAI Response Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, config)
    return True

async def async_setup_entry(
        hass: HomeAssistant,
        entry: config_entries.ConfigEntry
    ) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

async def options_update_listener(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry
    ):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
        hass: HomeAssistant,
        entry: config_entries.ConfigEntry
    ) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug(entry_data)

        # Remove options_update_listener.
        entry_data["unsub_options_update_listener"]()

    return unload_ok

# async def async_get_options_flow(config_entry):
#     """Get the options flow for this handler."""
#     return OpenAIResponseCustomConfigFlow(config_entry)

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
 
