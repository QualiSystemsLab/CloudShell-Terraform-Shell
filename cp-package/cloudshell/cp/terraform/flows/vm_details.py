from logging import Logger

from cloudshell.cp.core.flows import AbstractVMDetailsFlow
from cloudshell.cp.core.request_actions.models import VmDetailsData
from cloudshell.cp.terraform.actions.vm_details import VMDetailsActions
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp


class TFGetVMDetailsFlow(AbstractVMDetailsFlow):
    def __init__(
        self,
        resource_conf,
        logger: Logger,
    ):
        super().__init__(logger)
        self._resource_conf = resource_conf

    def _get_vm_details(self, deployed_app: BaseTFDeployedApp) -> VmDetailsData:
        return VMDetailsActions(
            si,
            self._resource_conf,
            self._logger,
            self._cancellation_manager,
        ).create(vm, deployed_app)
