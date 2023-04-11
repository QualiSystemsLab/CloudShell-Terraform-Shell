import warnings
from typing import Optional

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionParamsModel,
    ConnectivityActionModel,
    VlanServiceModel,
)
from pydantic import Field


class TFVlanServiceModel(VlanServiceModel):
    port_group_name: Optional[str] = Field(None, alias="Port Group Name")

    def __getattribute__(self, item):
        if "port_group_name" == item:
            msg = (
                "'Port Group Name' attribute is deprecated, "
                "use 'Virtual Network' instead"
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
        return super().__getattribute__(item)


class TFConnectionParamsModel(ConnectionParamsModel):
    vlan_service_attrs: TFVlanServiceModel = Field(..., alias="vlanServiceAttributes")


class TFConnectivityActionModel(ConnectivityActionModel):
    connection_params: TFConnectionParamsModel = Field(..., alias="connectionParams")
