from __future__ import annotations

from logging import Logger

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.rollback import RollbackCommand, RollbackCommandsManager
from cloudshell.cp.terraform.handlers.datastore_handler import DatastoreHandler
from cloudshell.cp.terraform.handlers.dc_handler import DcHandler
from cloudshell.cp.terraform.handlers.resource_pool import ResourcePoolHandler
from cloudshell.cp.terraform.handlers.TF_path import TFPath
from cloudshell.cp.terraform.handlers.vm_handler import VmHandler
from cloudshell.cp.terraform.resource_config import TFResourceConfig
from cloudshell.cp.terraform.utils.ovf_tool import OVFToolScript


class DeployVMFromImageCommand(RollbackCommand):
    def __init__(
        self,
        rollback_manager: RollbackCommandsManager,
        cancellation_manager: CancellationContextManager,
        resource_conf: TFResourceConfig,
        TF_image: str,
        TF_image_arguments: list[str],
        vm_name: str,
        vm_resource_pool: ResourcePoolHandler,
        vm_storage: DatastoreHandler,
        vm_folder_path: TFPath,
        dc: DcHandler,
        logger: Logger,
    ):
        super().__init__(
            rollback_manager=rollback_manager, cancellation_manager=cancellation_manager
        )
        self._logger = logger
        self._resource_conf = resource_conf
        self._TF_image = TF_image
        self._TF_image_arguments = TF_image_arguments
        self._vm_name = vm_name
        self._vm_resource_pool = vm_resource_pool
        self._vm_storage = vm_storage
        self._vm_folder_path = vm_folder_path
        self._dc = dc
        self._logger = logger
        self._deployed_vm: VmHandler | None = None

    def _execute(self) -> VmHandler:
        ovf_tool_script = OVFToolScript(
            ovf_tool_path=self._resource_conf.ovf_tool_path,
            datacenter=self._resource_conf.default_datacenter,
            vm_cluster=self._resource_conf.vm_cluster,
            vm_storage=self._vm_storage.name,
            vm_folder=str(self._vm_folder_path),
            vm_resource_pool=self._resource_conf.vm_resource_pool,
            vm_name=self._vm_name,
            TF_image=self._TF_image,
            custom_args=self._TF_image_arguments,
            TF_user=self._resource_conf.user,
            TF_password=self._resource_conf.password,
            TF_host=self._resource_conf.address,
            logger=self._logger,
        )
        ovf_tool_script.run()

        path = self._vm_folder_path + self._vm_name
        vm = self._dc.get_vm_by_path(path)
        self._deployed_vm = vm
        return vm

    def rollback(self):
        if self._deployed_vm:
            self._deployed_vm.delete()
