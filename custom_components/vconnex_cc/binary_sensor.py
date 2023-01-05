"""Support for Vconnex Sensor."""

from __future__ import annotations

from types import SimpleNamespace

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_SAFETY,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DispatcherSignal
from .entity import EntityDescListResolver, EntityDescResolver, VconnexEntity
from .vconnex_wrap import HomeAssistantVconnexData


class ParamInfoExt(SimpleNamespace):
    """Param Infomation Extend."""

    device_class: str


ENTITY_DESC_EXT_MAP = {
    3043: [
        BinarySensorEntityDescription(
            key="eleak",
            device_class=DEVICE_CLASS_SAFETY,
        ),
    ], 
    3052: [
        BinarySensorEntityDescription(
            key="eleak",
            device_class=DEVICE_CLASS_SAFETY,
        ),
    ]
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
    if (device_type := int(device.deviceTypeCode)) in ENTITY_DESC_EXT_MAP:
        entity_desc_ext = ENTITY_DESC_EXT_MAP[device_type].get(key)
        if entity_desc_ext is not None:
            for attr in vars(entity_desc_ext):
                attr_val = getattr(entity_desc_ext, attr)
                if attr_val is not None:
                    param_dict[attr] = attr_val
            return param_dict
    return None


DEVICE_TYPE_SET: set[int] = set(ENTITY_DESC_EXT_MAP.keys())
DEVICE_PARAM_TYPE_SET: set[int] = {}
ENTITY_DESC_RESOLVER = EntityDescResolver.of(
    BinarySensorEntityDescription
).with_additional_param_func(append_entity_desc_ext)

ENTITY_DESC_LIST_RESOLVER_LIST = [
    EntityDescListResolver(DEVICE_TYPE_SET, DEVICE_PARAM_TYPE_SET, ENTITY_DESC_RESOLVER)
]


class VconnexBinarySensorEntity(VconnexEntity, BinarySensorEntity):
    """Vconnex Binary Sensor Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Create Vconnex Binary Sensor Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        self._attr_unique_id = f"{super().unique_id}.{description.key}"
        self.entity_id = self._attr_unique_id

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.get_data(
            param=self.entity_description.key, converter=lambda val, entity: val != 0
        )


TargetEntity = VconnexBinarySensorEntity


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
