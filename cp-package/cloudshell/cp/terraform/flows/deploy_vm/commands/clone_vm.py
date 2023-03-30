from __future__ import annotations

from contextlib import suppress
from logging import Logger

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.rollback import RollbackCommand, RollbackCommandsManager

from cloudshell.cp.terraform.handlers.config_spec_handler import ConfigSpecHandler
from cloudshell.cp.terraform.handlers.datastore_handler import DatastoreHandler
from cloudshell.cp.terraform.handlers.folder_handler import (
    FolderHandler,
    FolderIsNotEmpty,
)
from cloudshell.cp.terraform.handlers.resource_pool import ResourcePoolHandler
from cloudshell.cp.terraform.handlers.snapshot_handler import SnapshotHandler
from cloudshell.cp.terraform.handlers.task import ON_TASK_PROGRESS_TYPE
from cloudshell.cp.terraform.handlers.vm_handler import VmHandler


class CloneVMCommand(RollbackCommand):
    def __init__(
        self,
        vm_template: VmHandler,
        rollback_manager: RollbackCommandsManager,
        cancellation_manager: CancellationContextManager,
        vm_name: str,
        vm_storage: DatastoreHandler,
        vm_folder: FolderHandler,
        logger: Logger,
        vm_resource_pool: ResourcePoolHandler | None = None,
        vm_snapshot: SnapshotHandler | None = None,
        config_spec: ConfigSpecHandler | None = None,
        on_task_progress: ON_TASK_PROGRESS_TYPE | None = None,
    ):
        super().__init__(
            rollback_manager=rollback_manager, cancellation_manager=cancellation_manager
        )
        self._vm_template = vm_template
        self._vm_name = vm_name
        self._vm_resource_pool = vm_resource_pool
        self._vm_storage = vm_storage
        self._vm_folder = vm_folder
        self._vm_snapshot = vm_snapshot
        self._config_spec = config_spec
        self._logger = logger
        self._on_task_progress = on_task_progress
        self._cloned_vm: VmHandler | None = None

    def _execute(self) -> VmHandler:
        try:
            vm = self._vm_template.clone_vm(
                vm_name=self._vm_name,
                vm_storage=self._vm_storage,
                vm_folder=self._vm_folder,
                vm_resource_pool=self._vm_resource_pool,
                snapshot=self._vm_snapshot,
                config_spec=self._config_spec,
                on_task_progress=self._on_task_progress,
            )
        except Exception:
            with suppress(FolderIsNotEmpty):
                self._vm_folder.destroy()
            raise
        else:
            self._cloned_vm = vm
            return vm

    def rollback(self):
        if self._cloned_vm:
            self._cloned_vm.delete()
        with suppress(FolderIsNotEmpty):
            self._vm_folder.destroy()
