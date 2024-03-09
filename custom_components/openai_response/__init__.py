"""
OpenAI Response - Custom Component Init File
"""
# from typing import Any, Dict
import logging
from openai import OpenAI
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .sensor import OpenAIResponseSensor, SENSOR_TYPES
from .entities import (
    OpenAIResponse
    # OpenAIResponseTextInput
)
from .const import (
    DOMAIN,
    DEFAULT_PERSONA,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS
)
_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant,config: dict) -> bool:
    """Set up is called when Home Assistant is loading our component."""
    hass.data.setdefault(DOMAIN, config)
    return True

# async def async_setup_entry(
#         hass: HomeAssistant,
#         entry: config_entries.ConfigEntry
#     ) -> bool:
#     """Set up platform from a ConfigEntry."""
#     hass.data.setdefault(DOMAIN, {})
#     hass_data = dict(entry.data)
#     # Registers update listener to update config entry when options are updated.
#     unsub_options_update_listener = entry.add_update_listener(options_update_listener)
#     # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
#     hass_data["unsub_options_update_listener"] = unsub_options_update_listener
#     hass.data[DOMAIN][entry.entry_id] = hass_data

#     # Forward the setup to the sensor platform.
#     hass.async_create_task(
#         hass.config_entries.async_forward_entry_setup(entry, "sensor")
#     )
#     return True

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry
    # async_add_entities: AddEntitiesCallback
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    # openai_response: OpenAIResponse = hass.data[DOMAIN]
    config = entry.as_dict()
    if config['data'].get('endpoint_type') == "custom":
        client = OpenAI(
            base_url=config['data'].get("url"),
            api_key="nokey"
        )
    else:
        client = OpenAI(
            base_url=config['data'].get("url"),
            api_key=config['data'].get("api_key")
        )

    sensor_config = {
        "name": config['data'].get("name"),
        "client": client,
        "model": config['data'].get("model"),
        "persona": config['options'].get("persona", DEFAULT_PERSONA),
        "temperature": config['options'].get("temperature", DEFAULT_TEMPERATURE),
        "max_tokens": config['options'].get("max_tokens", DEFAULT_MAX_TOKENS)
    }

    config = hass.data[DOMAIN][entry.entry_id]
    if entry.options:
        config.update(entry.options)
    _LOGGER.debug("OpenAI Response Sensor Config: %s", config)

    entity_list = [
            OpenAIResponseSensor(
                hass,
                description,
                entry.entry_id,
                **sensor_config
            ) for description in SENSOR_TYPES
    ]
    # unique_name = f"OpenAI Response Input {entry.entry_id}"
    # input_text_config = {
    #     "name": unique_name,
    #     "state": "",
    #     "icon": "mdi:keyboard"
    # }
    # entity_list.append(OpenAIResponseTextInput(input_text_config))
    async_add_entities(entity_list)

async def options_update_listener(hass: HomeAssistant,config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant,entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("OpenAI Response Sensor Unloading Entry: %s",entry_data)

        # Remove options_update_listener.
        entry_data["unsub_options_update_listener"]()

    return unload_ok

# async def async_get_system_health_info(hass: HomeAssistant) -> Dict[str, Any]:
#     """Return information for the system health panel."""
#     # Define your custom health info here
#     health_info = {}
#     custom_component_info = {}
#     custom_component_info['status'] = STATE_OK
#     health_info['OpenAI Response Sensor'] = custom_component_info
#     return health_info

# async def async_get_options_flow(config_entry):
#     """Get the options flow for this handler."""
#     return OpenAIResponseCustomConfigFlow(config_entry)
