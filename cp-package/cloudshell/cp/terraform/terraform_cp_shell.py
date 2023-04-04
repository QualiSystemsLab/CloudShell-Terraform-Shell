import logging

from cloudshell.cp.terraform.handlers.cp_backend_handler import CPBackendHandler
from cloudshell.cp.terraform.handlers.provider_handler import CPProviderHandler
from cloudshell.cp.terraform.handlers.tf_handler import CPTfProcExec
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.iac.terraform.services.local_dir_service import LocalDir
from cloudshell.iac.terraform.services.object_factory import ObjectFactory
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler
from cloudshell.iac.terraform.tagging.tags import TagsManager


class TerraformCPShell:
    def __init__(
            self,
            resource_config: TerraformResourceConfig,
            logger: logging.Logger,
            tag_manager: TagsManager,
            sandbox_id: str,
    ):

        self._resource_config = resource_config
        self._tag_manager = tag_manager
        self._logger = logger
        self._sandbox_id = sandbox_id
        self._backend_handler = CPBackendHandler(self._resource_config, self._logger)
        self._provider_handler = CPProviderHandler(self._resource_config, self._logger)

    def execute_terraform(self, deploy_app: VMFromTerraformGit, vm_name):
        tf_proc_executer = CPTfProcExec(
            self._resource_config,
            self._sandbox_id,
            self._logger,
            self._backend_handler,
            self._tag_manager
        )

        try:
            self._provider_handler.initialize_provider(deploy_app)
            tf_proc_executer.init_terraform(deploy_app, vm_name)
            tf_proc_executer.tag_terraform(deploy_app)
            tf_proc_executer.plan_terraform(deploy_app, vm_name)
            tf_proc_executer.apply_terraform()
            return tf_proc_executer.save_terraform_outputs()
            # self._handle_error_output(shell_helper, "This Terraform Module has been successfully deployed but "
            #                                             "destroy failed. Please destroy successfully before running "
            #                                             "execute again.")
        finally:
            if self._resource_config.remote_state_provider:
                tf_proc_executer.delete_local_temp_dir(deploy_app)

    def destroy_terraform(self, deployed_app: BaseTFDeployedApp):
        # initialize a _logger if _logger wasn't passed during init

        tf_proc_executer = CPTfProcExec(
            self._resource_config,
            self._sandbox_id,
            self._logger,
            self._backend_handler,
            self._tag_manager
        )
        # if not tf_working_dir:
        #     self._handle_error_output(shell_helper, "Destroy failed due to missing local directory")

        try:
            self._provider_handler.initialize_provider(deployed_app)
            tf_proc_executer.init_terraform(deployed_app)
            tf_proc_executer.destroy_terraform(deployed_app)
        finally:
            if self._resource_config.remote_state_provider:
                tf_proc_executer.delete_local_temp_dir(deployed_app)

    # def _validate_remote_backend_or_existing_working_dir(self, sandbox_data_handler, shell_helper):
    #     if not self._resource_config.remote_state_provider and \
    #             not LocalDir.does_working_dir_exists(sandbox_data_handler.get_tf_working_dir()):
    #         self._handle_error_output(shell_helper, f"Missing local folder {sandbox_data_handler.get_tf_working_dir()}")

    # @staticmethod
    # def _destroy_passed(sandbox_data_handler):
    #     return sandbox_data_handler.get_status(DESTROY_STATUS) == DESTROY_PASSED
    #
    # @staticmethod
    # def _using_remote_state(shell_helper) -> bool:
    #     return bool(shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER))
    #
    # @staticmethod
    # def _handle_error_output(shell_helper: ShellHelperObject, err_msg: str):
    #     shell_helper.sandbox_messages.write_error_message(err_msg)
    #     raise Exception(err_msg)
