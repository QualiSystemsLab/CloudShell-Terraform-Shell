from logging import Logger

from cloudshell.cp.core.flows import AbstractVMDetailsFlow
from cloudshell.cp.core.request_actions.models import VmDetailsData
from cloudshell.cp.terraform.actions.vm_details import VMDetailsActions
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.terraform_cp_shell import TerraformCPShell


class TFGetVMDetailsFlow(AbstractVMDetailsFlow):
    def __init__(
        self,
        resource_conf,
        logger: Logger,
        sandbox_id: str,
    ):
        super().__init__(logger)
        self._resource_conf = resource_conf
        self.tf_executor = TerraformCPShell(
            resource_config=resource_conf,
            logger=self._logger,
            sandbox_id=sandbox_id,
        )

    def _get_vm_details(self, deployed_app: BaseTFDeployedApp) -> VmDetailsData:
        tf_outputs = self.tf_executor.refresh_terraform(deployed_app)
        return tf_outputs.get_vm_details_data(self._resource_conf)
        # return VMDetailsActions(
        #     self._resource_conf,
        #     deployed_app.name,
        #     tf_outputs,
        #     deployed_app.vmdetails.uid,
        #     self._logger,
        # ).create()
