"""Constants for the Vconnex integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN

DOMAIN = "vconnex_cc"
DOMAIN_NAME = "Vconnex CC"
PROJECT_CODE = "HASS"

PLATFORMS = [
    SWITCH_DOMAIN,
    SENSOR_DOMAIN,
    BINARY_SENSOR_DOMAIN,
    COVER_DOMAIN,
]

DEFAULT_ENDPOINT = "https://hass-api.vconnex.vn"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_USER_ID = "user_id"
CONF_PROJECT_NAME = "project_name"
CONF_USER_NAME = "user_name"
CONF_PASSWORD = "password"
CONF_ENDPOINT = "endpoint"
CONF_COUNTRY = "country"


class DispatcherSignal:
    """DispatcherSignal."""

    DEVICE_ADDED = f"{DOMAIN}.device_added"
    DEVICE_UPDATED = f"{DOMAIN}.device_updated"
    DEVICE_REMOVED = f"{DOMAIN}.device_removed"


class CommandName:
    """Device command name."""

    SET_DATA = "CmdSetData"
    GET_DATA = "CmdGetData"


class ParamType:
    """Device Param Type."""

    NONE = 0
    ON_OFF = 1
    OPEN_CLOSE = 2
    YES_NO = 3
    ALERT = 4
    MOVE_NOMOVE = 5
    RAW_VALUE = 6


PARAM_TYPES = [
    ParamType.NONE,
    ParamType.ON_OFF,
    ParamType.OPEN_CLOSE,
    ParamType.YES_NO,
    ParamType.ALERT,
    ParamType.MOVE_NOMOVE,
    ParamType.RAW_VALUE,
]
