"""
OpenAI Response - Validation Functions
"""
import logging
from openai import OpenAI
from .const import (
    DEFAULT_MODEL
)

_LOGGER = logging.getLogger(__name__)

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
        _LOGGER.debug(response.model_dump_json())
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
        _LOGGER.debug(response.model_dump_json())
    except Exception as exc:
        _LOGGER.error(str(exc))
        raise ValueError from exc
