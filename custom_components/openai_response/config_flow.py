#from copy import deepcopy
import logging
from typing import Any, Dict, Optional
from openai import OpenAI
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)
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

AUTH_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_URL): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string
    }
)
DETAILS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PERSONA, default=DEFAULT_PERSONA): cv.string,
        vol.Required(CONF_KEEPHISTORY, default=DEFAULT_KEEP_HISTORY): cv.boolean,
        vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): cv.positive_float,
        vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): cv.positive_int
    }
)

# OPTIONS_SHCEMA = vol.Schema(
#     {
#         vol.Optional(CONF_NAME, default="foo"): cv.string
#     }
# )

async def validate_openai_auth(api_key: str) -> None:
    """Validates OpenAI auth.

    Raises a ValueError if the API Key is invalid.
    """
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            engine="davinci",
            prompt="This is a connection test.",
            max_tokens=5
        )
    except Exception as exc:
        raise ValueError from exc

async def validate_custom_llm(base_url: str) -> None:
    """Validates custom LLM connectivity.

    Raises a ValueError if the machine cannot be reached.
    """
    client = OpenAI(base_url=base_url, api_key="nokey")
    try:
        response = client.chat.completions.create(
            engine="davinci",
            prompt="This is a connection test.",
            max_tokens=5
        )
    except Exception as exc:
        raise ValueError from exc

class OpenAIResponseCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """OpenAI Response custom config flow."""
    VERSION = 1
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        data_schema = {}
        data_schema["endpoint_type"] = selector({
            "select": {
                "options": ["OpenAI", "Custom"],
            }
        })
        if user_input is not None:
            self.user_info = user_input
            _LOGGER.info(self.user_info)

            if self.user_info.get(CONF_ENDPOINT_TYPE) == "openai":
                return await self.async_step_setup()
            #return await self.async_step_setup()
        
            # if not errors:
            #     pass
                # Input is valid, set data.
                #self.data = user_input
                # Return the form of the next step.
                #return await self.async_step_details()

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_setup(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}
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
        
        return self.async_show_form(
            step_id="setup", data_schema=AUTH_SCHEMA, errors=errors
        )

    async def async_step_details(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to settup openai details."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Validate the path.
            # try:
            #     await validate_path(
            #         user_input[CONF_PATH], self.data[CONF_ACCESS_TOKEN], self.hass
            #     )
            # except ValueError:
            #     errors["base"] = "invalid_path"

            if not errors:
                # Input is valid, set data.
                self.data[CONF_PERSONA] = user_input[CONF_PERSONA]
                self.data[CONF_KEEPHISTORY] = user_input[CONF_KEEPHISTORY]
                self.data[CONF_TEMPERATURE] = user_input[CONF_TEMPERATURE]
                self.data[CONF_MAX_TOKENS] = user_input[CONF_MAX_TOKENS]

                # User is done with entering settings, create the config entry.
                return self.async_create_entry(title="OpenAI Response", data=self.data)

        return self.async_show_form(
            step_id="details", data_schema=DETAILS_SCHEMA, errors=errors
        )

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Get the options flow for this handler."""
    #     return OptionsFlowHandler(config_entry)


# class OptionsFlowHandler(config_entries.OptionsFlow):
#     """Handles options flow for the component."""

#     def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
#         self.config_entry = config_entry

#     async def async_step_init(
#         self, user_input: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """Manage the options for the custom component."""
#         errors: Dict[str, str] = {}
#         # Grab all configured repos from the entity registry so we can populate the
#         # multi-select dropdown that will allow a user to remove a repo.
#         entity_registry = async_get(self.hass)
#         entries = async_entries_for_config_entry(
#             entity_registry, self.config_entry.entry_id
#         )
#         # Default value for our multi-select.
#         all_repos = {e.entity_id: e.original_name for e in entries}
#         repo_map = {e.entity_id: e for e in entries}

#         if user_input is not None:
#             updated_repos = deepcopy(self.config_entry.data[CONF_REPOS])

#             # Remove any unchecked repos.
#             removed_entities = [
#                 entity_id
#                 for entity_id in repo_map.keys()
#                 if entity_id not in user_input["repos"]
#             ]
#             for entity_id in removed_entities:
#                 # Unregister from HA
#                 entity_registry.async_remove(entity_id)
#                 # Remove from our configured repos.
#                 entry = repo_map[entity_id]
#                 entry_path = entry.unique_id
#                 updated_repos = [e for e in updated_repos if e["path"] != entry_path]

#             if user_input.get(CONF_PATH):
#                 # Validate the path.
#                 access_token = self.hass.data[DOMAIN][self.config_entry.entry_id][
#                     CONF_ACCESS_TOKEN
#                 ]
#                 try:
#                     await validate_path(user_input[CONF_PATH], access_token, self.hass)
#                 except ValueError:
#                     errors["base"] = "invalid_path"

#                 if not errors:
#                     # Add the new repo.
#                     updated_repos.append(
#                         {
#                             "path": user_input[CONF_PATH],
#                             "name": user_input.get(CONF_NAME, user_input[CONF_PATH]),
#                         }
#                     )

#             if not errors:
#                 # Value of data will be set on the options property of our config_entry
#                 # instance.
#                 return self.async_create_entry(
#                     title="",
#                     data={CONF_REPOS: updated_repos},
#                 )

#         options_schema = vol.Schema(
#             {
#                 vol.Optional("repos", default=list(all_repos.keys())): cv.multi_select(
#                     all_repos
#                 ),
#                 vol.Optional(CONF_PATH): cv.string,
#                 vol.Optional(CONF_NAME): cv.string,
#             }
#         )
#         return self.async_show_form(
#             step_id="init", data_schema=options_schema, errors=errors
#         )