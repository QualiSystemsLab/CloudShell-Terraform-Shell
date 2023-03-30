from __future__ import annotations

from typing import TYPE_CHECKING, Union

from cloudshell.cp.core.request_actions.models import (
    VmDetailsData,
    VmDetailsNetworkInterface,
    VmDetailsProperty,
)

from cloudshell.cp.terraform.actions.vm_network import VMNetworkActions
from cloudshell.cp.terraform.handlers.si_handler import SiHandler
from cloudshell.cp.terraform.handlers.vm_handler import PowerState, VmHandler
from cloudshell.cp.terraform.models.deploy_app import (
    BaseTFDeployApp,
    VMFromImageDeployApp,
    VMFromLinkedCloneDeployApp,
    VMFromTemplateDeployApp,
    VMFromVMDeployApp,
)
from cloudshell.cp.terraform.models.deployed_app import (
    BaseTFDeployedApp,
    StaticTFDeployedApp,
    VMFromImageDeployedApp,
    VMFromLinkedCloneDeployedApp,
    VMFromTemplateDeployedApp,
    VMFromVMDeployedApp,
)
from cloudshell.cp.terraform.utils.bytes_converter import format_bytes

if TYPE_CHECKING:
    from logging import Logger

    from cloudshell.cp.core.cancellation_manager import CancellationContextManager

    from cloudshell.cp.terraform.resource_config import TFResourceConfig


APP_MODEL_TYPES = Union[
    BaseTFDeployApp, BaseTFDeployedApp, StaticTFDeployedApp
]


class VMDetailsActions(VMNetworkActions):
    def __init__(
        self,
        si: SiHandler,
        resource_conf: TFResourceConfig,
        logger: Logger,
        cancellation_manager: CancellationContextManager,
    ):
        self._si = si
        super().__init__(resource_conf, logger, cancellation_manager)

    @staticmethod
    def _prepare_common_vm_instance_data(vm: VmHandler) -> list[VmDetailsProperty]:
        data = [
            VmDetailsProperty(key="CPU", value=f"{vm.num_cpu} vCPU"),
            VmDetailsProperty(key="Memory", value=format_bytes(vm.memory_size)),
            VmDetailsProperty(key="Guest OS", value=vm.guest_os),
            VmDetailsProperty(key="Managed Object Reference ID", value=vm._moId),
        ]
        hdd_data = [
            VmDetailsProperty(
                key=f"{d.name} Size", value=format_bytes(d.capacity_in_bytes)
            )
            for d in vm.disks
        ]
        return data + hdd_data

    def _prepare_vm_network_data(
        self,
        vm: VmHandler,
        app_model: APP_MODEL_TYPES,
    ) -> list[VmDetailsNetworkInterface]:
        """Prepare VM Network data."""
        self._logger.info(f"Preparing VM Details network data for the {vm}")
        network_interfaces = []

        if isinstance(app_model, StaticTFDeployedApp):
            # try to get VM IP without waiting
            primary_ip = self.get_vm_ip(vm, timeout=0)
        elif vm.power_state is PowerState.ON:
            # try to get VM IP without waiting, use IP regex if present
            primary_ip = self.get_vm_ip(vm, ip_regex=app_model.ip_regex, timeout=0)
        else:
            primary_ip = None

        for vnic in vm.vnics:
            network = vnic.network
            is_predefined = network.name in self._resource_conf.reserved_networks
            vlan_id = vm.get_network_vlan_id(network)

            if vlan_id and (self.is_quali_network(network.name) or is_predefined):
                vnic_ip = vnic.ipv4
                is_primary = primary_ip == vnic_ip if vnic_ip and primary_ip else False

                network_data = [
                    VmDetailsProperty(key="IP", value=vnic_ip),
                    VmDetailsProperty(key="MAC Address", value=vnic.mac_address),
                    VmDetailsProperty(key="Network Adapter", value=vnic.name),
                    VmDetailsProperty(key="Port Group Name", value=network.name),
                ]

                interface = VmDetailsNetworkInterface(
                    interfaceId=vnic.mac_address,
                    networkId=str(vlan_id),
                    isPrimary=is_primary,
                    isPredefined=is_predefined,
                    networkData=network_data,
                    privateIpAddress=vnic_ip,
                )
                network_interfaces.append(interface)

        return network_interfaces

    @staticmethod
    def prepare_vm_from_vm_details(
        deploy_app: VMFromVMDeployApp | VMFromVMDeployedApp,
    ) -> list[VmDetailsProperty]:
        return [
            VmDetailsProperty(
                key="Cloned VM Name",
                value=deploy_app.TF_vm,
            ),
        ]

    @staticmethod
    def prepare_vm_from_template_details(
        deploy_app: VMFromTemplateDeployApp | VMFromTemplateDeployedApp,
    ) -> list[VmDetailsProperty]:
        return [
            VmDetailsProperty(
                key="Template Name",
                value=deploy_app.TF_template,
            ),
        ]

    @staticmethod
    def prepare_vm_from_clone_details(
        deploy_app: VMFromLinkedCloneDeployApp | VMFromLinkedCloneDeployedApp,
    ) -> list[VmDetailsProperty]:
        return [
            VmDetailsProperty(
                key="Cloned VM Name",
                value=(
                    f"{deploy_app.TF_vm} "
                    f"(snapshot: {deploy_app.TF_vm_snapshot})"
                ),
            ),
        ]

    @staticmethod
    def prepare_vm_from_image_details(
        deploy_app: VMFromImageDeployApp | VMFromImageDeployedApp,
    ) -> list[VmDetailsProperty]:
        return [
            VmDetailsProperty(
                key="Base Image Name",
                value=deploy_app.TF_image.split("/")[-1],
            ),
        ]

    @staticmethod
    def prepare_static_vm_details(
        deployed_app: StaticTFDeployedApp,
    ) -> list[VmDetailsProperty]:
        return []

    def _get_extra_instance_details(
        self, app_model: APP_MODEL_TYPES
    ) -> list[VmDetailsProperty]:
        if isinstance(app_model, (VMFromVMDeployApp, VMFromVMDeployedApp)):
            res = self.prepare_vm_from_vm_details(app_model)
        elif isinstance(
            app_model, (VMFromTemplateDeployApp, VMFromTemplateDeployedApp)
        ):
            res = self.prepare_vm_from_template_details(app_model)
        elif isinstance(
            app_model, (VMFromLinkedCloneDeployApp, VMFromLinkedCloneDeployedApp)
        ):
            res = self.prepare_vm_from_clone_details(app_model)
        elif isinstance(app_model, (VMFromImageDeployApp, VMFromImageDeployedApp)):
            res = self.prepare_vm_from_image_details(app_model)
        elif isinstance(app_model, StaticTFDeployedApp):
            res = self.prepare_static_vm_details(app_model)
        else:
            raise NotImplementedError(f"Not supported type {type(app_model)}")
        return res

    def create(
        self,
        vm: VmHandler,
        app_model: APP_MODEL_TYPES,
    ) -> VmDetailsData:
        try:
            app_name = app_model.app_name  # DeployApp
        except AttributeError:
            app_name = app_model.name  # DeployedApp

        try:
            instance_details = self._prepare_common_vm_instance_data(vm)
            instance_details.extend(self._get_extra_instance_details(app_model))
            network_details = self._prepare_vm_network_data(vm, app_model)
        except Exception as e:
            self._logger.exception("Failed to created VM Details:")
            details = VmDetailsData(appName=app_name, errorMessage=str(e))
        else:
            details = VmDetailsData(
                appName=app_name,
                vmInstanceData=instance_details,
                vmNetworkData=network_details,
            )
        self._logger.info(f"VM Details: {details}")
        return details
