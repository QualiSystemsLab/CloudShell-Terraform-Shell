import logging

from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.iac.terraform.services.local_dir_service import LocalDir
from cloudshell.iac.terraform.services.object_factory import ObjectFactory
from cloudshell.iac.terraform.services.provider_handler import ProviderHandler


class TerraformCPHandler:
    def __init__(self,
            logger: logging.Logger,
            config: TerraformResourceConfig
    ):
        # self._tf_service = ObjectFactory.create_tf_service(driver_context)
        self._logger = logger
        self._config = config
        self._provider_handler = ProviderHandler(self._logger)

    # def execute_terraform(self):
    #     # shell_helper = ObjectFactory.create_shell_helper(self._tf_service,
    #     #                                                  self._context,
    #     #                                                  self._config, logger)
    #     # sandbox_data_handler = SandboxDataHandler(shell_helper)
    #     tf_working_dir = LocalDir.prepare_tf_working_dir(logger,
    #                                                      sandbox_data_handler,
    #                                                      shell_helper)
    #
    #     self._execute_procedure(sandbox_data_handler, shell_helper, tf_working_dir)

    def deploy_tf(self):

        try:
            tf_proc_executer = ObjectFactory.create_tf_proc_executer(self._config,
                                                                     sandbox_data_handler,
                                                                     shell_helper,
                                                                     tf_working_dir)
            if tf_proc_executer.can_execute_run():
                self._provider_handler.initialize_provider(shell_helper)
                tf_proc_executer.init_terraform()
                tf_proc_executer.tag_terraform()
                tf_proc_executer.plan_terraform()
                tf_proc_executer.apply_terraform()
                tf_proc_executer.save_terraform_outputs()
            else:
                self._handle_error_output(shell_helper,
                                          "This Terraform Module has been successfully deployed but "
                                          "destroy failed. Please destroy successfully before running "
                                          "execute again.")
        finally:
            if self._using_remote_state(shell_helper):
                LocalDir.delete_local_temp_dir(sandbox_data_handler, tf_working_dir)

    def destroy_tf(self):
        tf_working_dir = LocalDir.prepare_tf_working_dir(logger,
                                                         sandbox_data_handler,
                                                         shell_helper)
        if not tf_working_dir:
            self._handle_error_output(shell_helper,
                                      "Destroy failed due to missing local directory")

        try:
            self._provider_handler.initialize_provider(shell_helper)
            tf_proc_executer = ObjectFactory.create_tf_proc_executer(self._config,
                                                                     sandbox_data_handler,
                                                                     shell_helper,
                                                                     tf_working_dir)
            if tf_proc_executer.can_destroy_run():
                tf_proc_executer.init_terraform()
                tf_proc_executer.destroy_terraform()
            else:
                self._handle_error_output(shell_helper,
                                          "Destroy blocked because APPLY was not yet executed")
        finally:
            if self._using_remote_state(shell_helper) or self._destroy_passed(
                    sandbox_data_handler):
                LocalDir.delete_local_temp_dir(sandbox_data_handler, tf_working_dir)

    def _validate_remote_backend_or_existing_working_dir(self, sandbox_data_handler,
                                                         shell_helper):
        if not shell_helper.attr_handler.get_attribute(
                ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER) and \
                not LocalDir.does_working_dir_exists(
                    sandbox_data_handler.get_tf_working_dir()):
            self._handle_error_output(shell_helper,
                                      f"Missing local folder {sandbox_data_handler.get_tf_working_dir()}")

    # @staticmethod
    # def _destroy_passed(sandbox_data_handler):
    #     return sandbox_data_handler.get_status(DESTROY_STATUS) == DESTROY_PASSED
    #
    # @staticmethod
    # def _using_remote_state(shell_helper) -> bool:
    #     return bool(shell_helper.attr_handler.get_attribute(
    #         ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER))
    #
    # @staticmethod
    # def _handle_error_output(shell_helper: ShellHelperObject, err_msg: str):
    #     shell_helper.sandbox_messages.write_error_message(err_msg)
    #     raise Exception(err_msg)
