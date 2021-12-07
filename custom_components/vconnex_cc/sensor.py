"""Support for Vconnex Sensor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    ELECTRIC_CURRENT_AMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, DispatcherSignal, ParamType
from .entity import EntityDescListResolver, EntityDescResolver, VconnexEntity
from .vconnex_wrap import HomeAssistantVconnexData

LOGGER = logging.getLogger(__name__)


@dataclass
class SensorEntityDescriptionExt(SensorEntityDescription):
    """Extend description of sensor entity."""

    value_converter: Callable[[Any, VconnexEntity], Any] | None = None
    extended_param: bool = False


ENTITY_DESC_EXT_MAP = {
    # Electric Meter
    3009: [
        SensorEntityDescriptionExt(
            key="Current",
            device_class=DEVICE_CLASS_CURRENT,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        ),
        SensorEntityDescriptionExt(
            key="Voltage",
            device_class=DEVICE_CLASS_VOLTAGE,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        ),
        SensorEntityDescriptionExt(
            key="Power",
            device_class=DEVICE_CLASS_POWER,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=POWER_WATT,
        ),
        SensorEntityDescriptionExt(
            key="EnergyCount",
            device_class=DEVICE_CLASS_ENERGY,
            state_class=STATE_CLASS_TOTAL_INCREASING,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        ),
        SensorEntityDescriptionExt(
            key="ExportEnergyCount",
            device_class=DEVICE_CLASS_ENERGY,
            state_class=STATE_CLASS_TOTAL_INCREASING,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        ),
        # extend param
        SensorEntityDescriptionExt(
            key="ConsumptionCountToday",
            device_class=DEVICE_CLASS_ENERGY,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            extended_param=True,
        ),
        SensorEntityDescriptionExt(
            key="ConsumptionCountThisMonth",
            device_class=DEVICE_CLASS_ENERGY,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            extended_param=True,
        ),
        SensorEntityDescriptionExt(
            key="ConsumptionCostThisMonth",
            state_class=STATE_CLASS_MEASUREMENT,
            extended_param=True,
        ),
        SensorEntityDescriptionExt(
            key="ExportCountToday",
            device_class=DEVICE_CLASS_ENERGY,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            extended_param=True,
        ),
        SensorEntityDescriptionExt(
            key="ExportCountThisMonth",
            device_class=DEVICE_CLASS_ENERGY,
            state_class=STATE_CLASS_MEASUREMENT,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            extended_param=True,
        ),
        SensorEntityDescriptionExt(
            key="ExportCostThisMonth",
            state_class=STATE_CLASS_MEASUREMENT,
            extended_param=True,
        ),
    ],
}


def fix_entity_desc_map():
    """Convert ENTITY_DESC_EXT_MAP object."""
    for device_type, desc_list in ENTITY_DESC_EXT_MAP.items():
        desc_list_map = {desc.key: desc for desc in desc_list}
        ENTITY_DESC_EXT_MAP[device_type] = desc_list_map


fix_entity_desc_map()


@callback
def append_entity_desc_ext(param_dict: dict, device: VconnexDevice) -> dict:
    """Append addition param info to entity description."""
    key = param_dict.get("key")
    device_type = int(device.deviceTypeCode)
    if device_type in ENTITY_DESC_EXT_MAP:
        entity_desc_ext = ENTITY_DESC_EXT_MAP[device_type].get(key)
        if entity_desc_ext is not None:
            for attr in vars(entity_desc_ext):
                attr_val = getattr(entity_desc_ext, attr)
                if attr_val is not None:
                    param_dict[attr] = attr_val
    return param_dict


DEVICE_TYPE_SET: set[int] = set(ENTITY_DESC_EXT_MAP.keys())
DEVICE_PARAM_TYPE_SET: set[int] = {ParamType.RAW_VALUE}
ENTITY_DESC_RESOLVER = EntityDescResolver.of(
    SensorEntityDescriptionExt
).with_additional_param_func(append_entity_desc_ext)

ENTITY_DESC_LIST_RESOLVER_LIST = [
    EntityDescListResolver(DEVICE_TYPE_SET, DEVICE_PARAM_TYPE_SET, ENTITY_DESC_RESOLVER)
]


class VconnexSensorEntity(VconnexEntity, SensorEntity):
    """Vconnex Sensor Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: SensorEntityDescriptionExt,
    ) -> None:
        """Create Vconnex Sensor Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        self._attr_unique_id = f"{super().unique_id}.{description.key}"
        self.entity_id = self._attr_unique_id

        if (
            hasattr(self.entity_description, "value_converter")
            and self.entity_description.value_converter is not None
        ):
            self.value_converter = self.entity_description.value_converter
        else:
            self.value_converter = None

    @property
    def native_value(self) -> StateType:
        """Get native value of sensor."""
        if self.entity_description.extended_param:
            return self._get_extended_data(
                self.entity_description.key, self.value_converter
            )

        return self.get_data(self.entity_description.key, self.value_converter)

    def _get_extended_data(
        self, param, converter: Callable[[Any, VconnexEntity], Any] = None
    ) -> Any:
        """Get data of ExtendedDeviceData message."""
        try:
            data_dict = self._get_device_data("ExtendedDeviceData")
            if data_dict is not None and "devV" in data_dict:
                d_values = data_dict.get("devV")
                for d_value in d_values:
                    if d_value.get("param") == param:
                        param_value = d_value.get("value")
                        return (
                            param_value
                            if converter is None
                            else converter(param_value, self)
                        )
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Something went wrong!!!")

        return None


TargetEntity = VconnexSensorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Async setup Home Assistant entry."""
    vconnex_data: HomeAssistantVconnexData = hass.data[DOMAIN][entry.entry_id]
    device_manager = vconnex_data.device_manager

    @callback
    def on_device_added(device_ids: list[str]) -> None:
        """Device added callback."""
        entities: list[Entity] = []
        for device_id in device_ids:
            device = device_manager.device_map[device_id]
            for description_list_resolver in ENTITY_DESC_LIST_RESOLVER_LIST:
                description_list = description_list_resolver.from_device(device)
                if len(description_list) > 0:
                    for description in description_list:
                        entities.append(
                            TargetEntity(
                                vconnex_device=device,
                                device_manager=device_manager,
                                description=description,
                            )
                        )
        async_add_entities(entities)

    async_dispatcher_connect(hass, DispatcherSignal.DEVICE_ADDED, on_device_added)
    on_device_added(device_ids=device_manager.device_map.keys())
