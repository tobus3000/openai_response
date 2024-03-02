"""Our domain (namespace) for storing config data in home assistant."""
DOMAIN = "openai_response"

"""Default values"""
DEFAULT_NAME = "hassio_openai_response"
DEFAULT_MODEL = "text-davinci-003"
DEFAULT_PERSONA = "You are a helpful assistant. Your answers are complete but short."
DEFAULT_KEEP_HISTORY = False
DEFAULT_TEMPERATURE = 0.9
DEFAULT_MAX_TOKENS = 300

"""Custom config parameters for this component (use in sensor.yaml)."""
CONF_ENDPOINT_TYPE = "endpoint_type"
CONF_MODEL = "model"
CONF_PERSONA = "persona"
CONF_KEEPHISTORY = "keep_history"
CONF_TEMPERATURE = "temperature"
CONF_MAX_TOKENS = "max_tokens"
