from __future__ import annotations

from collections.abc import Iterator

# from cloudshell.cp.terraform.constants import DEPLOYED_APPS_FOLDER
# from cloudshell.cp.terraform.handlers.TF_path import TFPath
# from cloudshell.cp.terraform.models.deploy_app import BaseTFDeployApp
# from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
# from cloudshell.cp.terraform._resource_config import TFResourceConfig


def is_vnic(device) -> bool:
    return isinstance(device, vim.vm.device.VirtualEthernetCard)


def is_virtual_disk(device) -> bool:
    return isinstance(device, vim.vm.device.VirtualDisk)


def is_virtual_scsi_controller(device) -> bool:
    return isinstance(device, vim.vm.device.VirtualSCSIController)


def get_device_key(device):
    return device.key


def get_all_devices(vm: vim.VirtualMachine):
    return vm.config.hardware.device


def get_vnics(vm: vim.VirtualMachine) -> Iterator[vim.vm.device.VirtualEthernetCard]:
    return filter(is_vnic, get_all_devices(vm))


def get_virtual_disks(vm: vim.VirtualMachine) -> Iterator[vim.vm.device.VirtualDisk]:
    return filter(is_virtual_disk, get_all_devices(vm))


def get_virtual_scsi_controllers(
    vm: vim.VirtualMachine,
) -> Iterator[vim.vm.device.VirtualSCSIController]:
    return filter(is_virtual_scsi_controller, get_all_devices(vm))


def get_vm_folder_path(
    model: BaseTFDeployApp | BaseTFDeployedApp,
    resource_conf: TFResourceConfig,
    reservation_id: str,
) -> TFPath:
    path = TFPath(model.vm_location or resource_conf.vm_location)
    path.append(DEPLOYED_APPS_FOLDER)
    path.append(reservation_id)
    return path
