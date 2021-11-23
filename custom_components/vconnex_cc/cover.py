"""Support for Vconnex Corver."""

from __future__ import annotations

from dataclasses import dataclass

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.cover import (
    DEVICE_CLASS_CURTAIN,
    CoverEntity,
    CoverEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CommandName, DispatcherSignal, ParamType
from .entity import EntityDescListResolver, EntityDescResolver, VconnexEntity
from .vconnex_wrap import HomeAssistantVconnexData


@dataclass
class CoverEntityDescriptionExt(CoverEntityDescription):
    """Cover entity info extend."""

    index: int = 0
    open_param: str = "curtain_open"
    close_param: str = "curtain_close"
    stop_param: str = "curtain_stop"
    open_position_param: str = "open_level"

    def __post_init__(self, **kwargs) -> None:
        """Init after create object."""
        if self.index != 0:
            self.open_param = self.__param_with_index(self.open_param, self.index)
            self.close_param = self.__param_with_index(self.close_param, self.index)
            self.stop_param = self.__param_with_index(self.stop_param, self.index)
            self.open_position_param = self.__param_with_index(
                self.open_position_param, self.index
            )

    @staticmethod
    def __param_with_index(param: str, index: int):
        param_segment = param.split("_")
        return f"{param_segment[0]}_{index}_{param_segment[1]}"


DEVICE_ENTITY_MAP = {
    3040: [
        CoverEntityDescriptionExt(
            key="cover", index=0, device_class=DEVICE_CLASS_CURTAIN
        )
    ],
    3041: [
        CoverEntityDescriptionExt(
            key="cover_1", index=0, device_class=DEVICE_CLASS_CURTAIN
        ),
        CoverEntityDescriptionExt(
            key="cover_2", index=2, device_class=DEVICE_CLASS_CURTAIN
        ),
    ],
    3042: [
        CoverEntityDescriptionExt(
            key="curtain_motor", index=0, device_class=DEVICE_CLASS_CURTAIN
        )
    ],
}


class EntityDescListResolverExt(EntityDescListResolver):
    """Entity Description List Resolver Extend."""

    def from_device(self, device: VconnexDevice) -> list:
        """Get entity description list from device."""
        device_type_code = int(device.deviceTypeCode)
        if device_type_code in self._accept_device_types:
            if device is not None and device_type_code in DEVICE_ENTITY_MAP:
                return DEVICE_ENTITY_MAP[device_type_code]
        return []


DEVICE_TYPE_SET: set[int] = set(DEVICE_ENTITY_MAP.keys())
DEVICE_PARAM_TYPE_SET: set[int] = {ParamType.ON_OFF, ParamType.OPEN_CLOSE}
ENTITY_DESC_RESOLVER = EntityDescResolver.of(CoverEntityDescriptionExt)

ENTITY_DESC_LIST_RESOLVER_LIST = [
    EntityDescListResolverExt(
        DEVICE_TYPE_SET, DEVICE_PARAM_TYPE_SET, ENTITY_DESC_RESOLVER
    )
]


class VconnexCoverEntity(VconnexEntity, CoverEntity):
    """Vconnex Cover Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: CoverEntityDescriptionExt,
    ) -> None:
        """Create Vconnex Cover Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        self._attr_unique_id = f"{super().unique_id}.{description.key}"
        self.entity_id = self._attr_unique_id
        if description.index != 0 and self._attr_name is not None:
            self._attr_name = f"{self._attr_name} {description.index}"

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover."""
        return self.get_data(self.entity_description.open_position_param)

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening or not."""
        return self.get_data(
            self.entity_description.open_param, lambda val, entity: int(val) != 0
        )

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing or not."""
        return self.get_data(
            self.entity_description.close_param, lambda val, entity: int(val) != 0
        )

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return (
            position == 0
            if (position := self.current_cover_position) is not None
            else None
        )

    def open_cover(self, **kwargs):
        """Open the cover."""
        self._send_command(
            CommandName.SET_DATA, {self.entity_description.open_param: 1}
        )

    def close_cover(self, **kwargs):
        """Close cover."""
        self._send_command(
            CommandName.SET_DATA, {self.entity_description.close_param: 1}
        )

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        param_dict = dict(kwargs)
        if "position" in param_dict:
            self._send_command(
                CommandName.SET_DATA,
                {self.entity_description.open_position_param: param_dict["position"]},
            )

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._send_command(
            CommandName.SET_DATA, {self.entity_description.stop_param: 1}
        )


TargetEntity = VconnexCoverEntity


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
