from __future__ import annotations

from collections.abc import Collection
from contextlib import suppress
from logging import Logger
from threading import Lock
from typing import TYPE_CHECKING

from cloudshell.shell.flows.connectivity.basic_flow import AbstractConnectivityFlow
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    AbstractParseConnectivityService,
)

from cloudshell.cp.terraform.exceptions import BaseTFException
from cloudshell.cp.terraform.handlers.dc_handler import DcHandler
from cloudshell.cp.terraform.handlers.managed_entity_handler import ManagedEntityNotFound
from cloudshell.cp.terraform.handlers.network_handler import (
    AbstractNetwork,
    DVPortGroupHandler,
    NetworkHandler,
    NetworkNotFound,
)
from cloudshell.cp.terraform.handlers.si_handler import SiHandler
from cloudshell.cp.terraform.handlers.switch_handler import (
    AbstractSwitchHandler,
    DvSwitchNotFound,
    PortGroupExists,
)
from cloudshell.cp.terraform.handlers.vm_handler import VmHandler
from cloudshell.cp.terraform.handlers.vsphere_api_handler import (
    NotEnoughPrivilegesListObjectTags,
)
from cloudshell.cp.terraform.handlers.vsphere_sdk_handler import VSphereSDKHandler
from cloudshell.cp.terraform.models.connectivity_action_model import (
    TFConnectivityActionModel,
)
from cloudshell.cp.terraform.resource_config import TFResourceConfig
from cloudshell.cp.terraform.utils.connectivity_helpers import (
    create_new_vnic,
    generate_port_group_name,
    get_available_vnic,
    get_existed_port_group_name,
    get_forged_transmits,
    get_mac_changes,
    get_promiscuous_mode,
    should_remove_port_group,
)

if TYPE_CHECKING:
    from cloudshell.cp.core.reservation_info import ReservationInfo


class DvSwitchNameEmpty(BaseTFException):
    def __init__(self):
        msg = (
            "For connectivity actions you have to specify default DvSwitch name in the "
            "resource or in every VLAN service"
        )
        super().__init__(msg)


class TFConnectivityFlow(AbstractConnectivityFlow):
    def __init__(
        self,
        resource_conf: TFResourceConfig,
        reservation_info: ReservationInfo,
        parse_connectivity_request_service: AbstractParseConnectivityService,
        logger: Logger,
    ):
        super().__init__(parse_connectivity_request_service, logger)
        self._resource_conf = resource_conf
        self._reservation_info = reservation_info
        self._si = SiHandler.from_config(resource_conf, logger)
        self._vsphere_client = VSphereSDKHandler.from_config(
            resource_config=self._resource_conf,
            reservation_info=self._reservation_info,
            logger=self._logger,
            si=self._si,
        )
        self._network_lock = Lock()

    def _validate_received_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> None:
        all_actions_with_switch = all(
            a.connection_params.vlan_service_attrs.switch_name for a in actions
        )
        if not self._resource_conf.default_dv_switch and not all_actions_with_switch:
            raise DvSwitchNameEmpty

    def _set_vlan(
        self, action: TFConnectivityActionModel
    ) -> ConnectivityActionResult:
        vlan_id = action.connection_params.vlan_id
        vc_conf = self._resource_conf
        dc = DcHandler.get_dc(vc_conf.default_datacenter, self._si)
        vm = dc.get_vm_by_uuid(action.custom_action_attrs.vm_uuid)
        default_network = dc.get_network(vc_conf.holding_network)
        self._logger.info(f"Start setting vlan {vlan_id} for the {vm}")

        switch = self._get_switch(dc, vm, action)
        with self._network_lock:
            network = self._get_or_create_network(dc, switch, action)
            if action.custom_action_attrs.vnic:
                vnic = vm.get_vnic(action.custom_action_attrs.vnic)
            else:
                vnic = get_available_vnic(
                    vm, default_network, vc_conf.reserved_networks
                )

            try:
                if not vnic:
                    create_new_vnic(vm, network)
                else:
                    vnic.connect(network)
            except Exception:
                if should_remove_port_group(network.name, action):
                    self._remove_network(network, vm)
                raise
        msg = f"Setting VLAN {vlan_id} successfully completed"
        return ConnectivityActionResult.success_result_vm(action, msg, vnic.mac_address)

    def _remove_vlan(
        self, action: TFConnectivityActionModel
    ) -> ConnectivityActionResult:
        vc_conf = self._resource_conf
        dc = DcHandler.get_dc(vc_conf.default_datacenter, self._si)
        vm = dc.get_vm_by_uuid(action.custom_action_attrs.vm_uuid)
        default_network = dc.get_network(vc_conf.holding_network)
        vnic = vm.get_vnic_by_mac(action.connector_attrs.interface)
        network = vnic.network
        self._logger.info(f"Start disconnecting {network} from the {vnic} on the {vm}")

        vnic.connect(default_network)

        with suppress(ManagedEntityNotFound):  # network can be already removed
            if should_remove_port_group(network.name, action):
                self._remove_network_tags(network)
                self._remove_network(network, vm)

        msg = "Removing VLAN successfully completed"
        return ConnectivityActionResult.success_result_vm(action, msg, vnic.mac_address)

    def _get_switch(
        self, dc: DcHandler, vm: VmHandler, action: TFConnectivityActionModel
    ) -> AbstractSwitchHandler:
        switch_name = (
            action.connection_params.vlan_service_attrs.switch_name
            or self._resource_conf.default_dv_switch
        )
        try:
            switch = dc.get_dv_switch(switch_name)
        except DvSwitchNotFound:
            switch = vm.get_v_switch(switch_name)
        return switch

    def _get_or_create_network(
        self,
        dc: DcHandler,
        switch: AbstractSwitchHandler,
        action: TFConnectivityActionModel,
    ) -> NetworkHandler | DVPortGroupHandler:
        pg_name = get_existed_port_group_name(action)
        if pg_name:
            network = dc.get_network(pg_name)
        else:
            network = self._create_network_based_on_vlan_id(dc, switch, action)
        return network

    @staticmethod
    def _validate_network(
        network: NetworkHandler | DVPortGroupHandler,
        switch: AbstractSwitchHandler,
        promiscuous_mode: bool,
        forged_transmits: bool,
        mac_changes: bool,
    ) -> None:
        pg = switch.get_port_group(network.name)
        if pg.allow_promiscuous != promiscuous_mode:
            raise BaseTFException(f"{pg} has incorrect promiscuous mode setting")
        if pg.forged_transmits != forged_transmits:
            raise BaseTFException(f"{pg} has incorrect forged transmits setting")
        if pg.mac_changes != mac_changes:
            raise BaseTFException(
                f"{pg} has incorrect MAC address changes setting"
            )

    def _create_network_based_on_vlan_id(
        self,
        dc: DcHandler,
        switch: AbstractSwitchHandler,
        action: TFConnectivityActionModel,
    ) -> AbstractNetwork:
        port_mode = action.connection_params.mode
        vlan_id = action.connection_params.vlan_id
        promiscuous_mode = get_promiscuous_mode(action, self._resource_conf)
        forged_transmits = get_forged_transmits(action, self._resource_conf)
        mac_changes = get_mac_changes(action, self._resource_conf)
        pg_name = generate_port_group_name(switch.name, vlan_id, port_mode)

        try:
            network = dc.get_network(pg_name)
        except NetworkNotFound:
            try:
                switch.create_port_group(
                    pg_name,
                    vlan_id,
                    port_mode,
                    promiscuous_mode,
                    forged_transmits,
                    mac_changes,
                )
            except PortGroupExists:
                pass
            port_group = switch.wait_port_group_appears(pg_name)
            network = dc.wait_network_appears(pg_name)
            if self._vsphere_client:
                try:
                    self._vsphere_client.assign_tags(obj=network)
                except Exception:
                    port_group.destroy()
                    raise
        else:
            # we validate only network created by the Shell
            self._validate_network(
                network, switch, promiscuous_mode, forged_transmits, mac_changes
            )
        return network

    @staticmethod
    def _remove_network(network: DVPortGroupHandler | NetworkHandler, vm: VmHandler):
        if network.wait_network_become_free():
            if isinstance(network, DVPortGroupHandler):
                network.destroy()
            else:
                vm.host.remove_port_group(network.name)

    def _remove_network_tags(self, network: AbstractNetwork):
        """Remove network's tags.

        NotEnoughPrivilegesListObjectTags error can mean that the network can be already
        removed. But we ought to check, if it isn't removed reraise the Tag's error.
        """
        if self._vsphere_client:
            try:
                self._vsphere_client.delete_tags(network)
            except NotEnoughPrivilegesListObjectTags:
                if not network.wait_network_disappears():
                    raise
