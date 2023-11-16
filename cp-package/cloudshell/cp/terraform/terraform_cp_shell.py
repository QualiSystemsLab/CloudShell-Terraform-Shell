import logging

from cloudshell.cp.terraform.handlers.cp_backend_handler import CPBackendHandler
from cloudshell.cp.terraform.handlers.tf_handler import CPTfProcExec
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.models.tf_deploy_result import TFDeployResult
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


class TerraformCPShell:
    def __init__(
        self,
        resource_config: TerraformResourceConfig,
        logger: logging.Logger,
        sandbox_id: str,
    ):

        self._resource_config = resource_config
        self._logger = logger
        self._sandbox_id = sandbox_id
        self._backend_handler = CPBackendHandler(self._resource_config, self._logger)

    def deploy_terraform(
        self,
        deploy_app: VMFromTerraformGit,
        vm_name: str,
    ) -> TFDeployResult:
        tf_proc_executer = CPTfProcExec(
            self._resource_config,
            self._sandbox_id,
            self._logger,
            self._backend_handler,
        )
        try:
            tf_proc_executer.init_terraform(deploy_app, vm_name)
            tf_proc_executer.tag_terraform(deploy_app)
            tf_proc_executer.plan_terraform(deploy_app, vm_name)
            tf_proc_executer.apply_terraform()
            return tf_proc_executer.save_terraform_outputs(deploy_app, vm_name)
            # Todo UUID - path to tfstate, if tfstate not found raise Error
            #  mentioning case with multiple ES servers
        except Exception as e:
            if not self._resource_config.remote_state_provider:
                tf_proc_executer.delete_local_temp_dir(deploy_app)
            raise

    def update_terraform(
        self,
        deployed_app: BaseTFDeployedApp,
        vm_name: str,
    ) -> TFDeployResult:
        tf_proc_executer = CPTfProcExec(
            self._resource_config,
            self._sandbox_id,
            self._logger,
            self._backend_handler,
        )

        try:
            path = deployed_app.vmdetails.uid
            tf_proc_executer.set_tf_working_dir(path)
            tf_proc_executer.init_terraform(deployed_app, vm_name, upgrade_init=True)
            tf_proc_executer.tag_terraform(deployed_app)
            tf_proc_executer.plan_terraform(deployed_app, vm_name)
            tf_proc_executer.apply_terraform()
            return tf_proc_executer.save_terraform_outputs(deployed_app, vm_name)
            # Todo UUID - path to tfstate, if tfstate not found raise Error
            #  mentioning case with multiple ES servers
        except:
            self._logger.error("Failed to modify Terraform")
            raise

    def refresh_terraform(self, deployed_app: BaseTFDeployedApp) -> TFDeployResult:
        tf_proc_executer = CPTfProcExec(
            self._resource_config,
            self._sandbox_id,
            self._logger,
            self._backend_handler,
        )

        try:
            vm_name = deployed_app.name
            path = deployed_app.vmdetails.uid
            tf_proc_executer.set_tf_working_dir(path)
            tf_proc_executer.init_terraform(deployed_app, vm_name, force_init=True)
            tf_proc_executer.show_terraform(deployed_app)
            return tf_proc_executer.save_terraform_outputs(deployed_app, vm_name)
            # Todo UUID - path to tfstate, if tfstate not found raise Error
            #  mentioning case with multiple ES servers
        except:
            self._logger.error("Failed to modify Terraform")
            raise

    def destroy_terraform(self, deployed_app: BaseTFDeployedApp):
        tf_proc_executer = CPTfProcExec(
            self._resource_config,
            self._sandbox_id,
            self._logger,
            self._backend_handler,
        )
        path = deployed_app.vmdetails.uid
        tf_proc_executer.set_tf_working_dir(path)

        try:
            tf_proc_executer.init_terraform(deployed_app, deployed_app.name, True)
            tf_proc_executer.destroy_terraform(deployed_app)
        finally:
            if not self._resource_config.remote_state_provider:
                tf_proc_executer.delete_local_temp_dir(deployed_app)
