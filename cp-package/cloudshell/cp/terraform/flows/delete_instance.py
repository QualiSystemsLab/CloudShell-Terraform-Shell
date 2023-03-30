from __future__ import annotations

from contextlib import suppress
from logging import Logger
from threading import Lock

from cloudshell.cp.core.reservation_info import ReservationInfo

# from cloudshell.cp.terraform.handlers.dc_handler import DcHandler
# from cloudshell.cp.terraform.handlers.folder_handler import (
#     FolderIsNotEmpty,
#     FolderNotFound,
# )
# from cloudshell.cp.terraform.handlers.si_handler import SiHandler
# from cloudshell.cp.terraform.handlers.vm_handler import VmNotFound
# from cloudshell.cp.terraform.handlers.vsphere_sdk_handler import VSphereSDKHandler
# from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
# from cloudshell.cp.terraform.resource_config import ShutdownMethod, TFResourceConfig
from cloudshell.cp.terraform.utils.vm_helpers import get_vm_folder_path

folder_delete_lock = Lock()


def _delete_tags(vsphere_client: VSphereSDKHandler | None, obj) -> None:
    if vsphere_client:
        vsphere_client.delete_tags(obj)


def delete_instance(
    deployed_app: BaseTFDeployedApp,
    resource_conf: TFResourceConfig,
    reservation_info: ReservationInfo,
    logger: Logger,
):
    si = SiHandler.from_config(resource_conf, logger)
    vsphere_client = VSphereSDKHandler.from_config(
        resource_config=resource_conf,
        reservation_info=reservation_info,
        logger=logger,
        si=si,
    )
    dc = DcHandler.get_dc(resource_conf.default_datacenter, si)

    vm_uuid = deployed_app.vmdetails.uid
    try:
        vm = dc.get_vm_by_uuid(vm_uuid)
    except VmNotFound:
        logger.warning(f"Trying to remove vm {vm_uuid} but it is not exists")
    else:
        _delete_tags(vsphere_client, vm)
        si.delete_customization_spec(vm.name)

        soft = resource_conf.shutdown_method is ShutdownMethod.SOFT
        vm.power_off(soft=soft)
        vm.delete()

    path = get_vm_folder_path(
        deployed_app, resource_conf, reservation_info.reservation_id
    )
    with folder_delete_lock:
        try:
            folder = dc.get_vm_folder(path)
        except FolderNotFound:
            pass
        else:
            _delete_tags(vsphere_client, folder)

            with suppress(FolderIsNotEmpty):
                folder.destroy()
