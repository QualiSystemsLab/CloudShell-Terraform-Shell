from contextlib import suppress

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.rollback import RollbackCommand, RollbackCommandsManager
from cloudshell.cp.terraform.handlers.custom_spec_handler import CustomSpecHandler
from cloudshell.cp.terraform.handlers.si_handler import CustomSpecNotFound, SiHandler
from cloudshell.cp.terraform.handlers.vm_handler import VmHandler
from cloudshell.cp.terraform.models.custom_spec import get_custom_spec_params
from cloudshell.cp.terraform.models.deploy_app import BaseTFDeployApp
from cloudshell.cp.terraform.utils.customization_params import prepare_custom_spec


class CreateVmCustomSpec(RollbackCommand):
    def __init__(
        self,
        rollback_manager: RollbackCommandsManager,
        cancellation_manager: CancellationContextManager,
        si: SiHandler,
        deploy_app: BaseTFDeployApp,
        vm_template: VmHandler,
        vm_name: str,
    ):
        super().__init__(rollback_manager, cancellation_manager)
        self._si = si
        self._deploy_app = deploy_app
        self._vm_template = vm_template
        self._vm_name = vm_name

    def _execute(self, *args, **kwargs) -> CustomSpecHandler:
        custom_spec_params = get_custom_spec_params(self._deploy_app, self._vm_template)
        spec = prepare_custom_spec(
            custom_spec_params,
            self._deploy_app.customization_spec,
            self._vm_template,
            self._vm_name,
            self._si,
        )
        return spec

    def rollback(self):
        with suppress(CustomSpecNotFound):
            self._si.delete_customization_spec(self._vm_name)
