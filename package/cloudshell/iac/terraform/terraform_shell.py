import logging
from contextlib import nullcontext

from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.iac.terraform import TerraformShellConfig
from cloudshell.iac.terraform.constants import DESTROY_STATUS, DESTROY_PASSED, ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.local_dir_service import LocalDir
from cloudshell.iac.terraform.services.provider_handler import ProviderHandler
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler
from cloudshell.iac.terraform.services.object_factory import ObjectFactory


class TerraformShell:
    # todo: add support to provide the info needed from attributes as parameters to the init (not shell attributes)
    def __init__(self, driver_context: ResourceCommandContext,
                 logger: logging.Logger = None, config: TerraformShellConfig = None):
        self._context = driver_context
        self._tf_service = ObjectFactory.create_tf_service(driver_context)
        self._logger = logger
        self._config = config or TerraformShellConfig()

    def execute_terraform(self):
        # initialize a logger if logger wasn't passed during init
        with nullcontext(self._logger) if self._logger else LoggingSessionContext(self._context) as logger:
            shell_helper = ObjectFactory.create_shell_helper(self._tf_service, self._context, self._config, logger)
            sandbox_data_handler = SandboxDataHandler(shell_helper)
            tf_working_dir = LocalDir.prepare_tf_working_dir(logger, sandbox_data_handler, shell_helper)

            self._execute_procedure(sandbox_data_handler, shell_helper, tf_working_dir)

    def _execute_procedure(self, sandbox_data_handler: SandboxDataHandler, shell_helper: ShellHelperObject,
                           tf_working_dir: str):
        try:
            tf_proc_executer = ObjectFactory.create_tf_proc_executer(self._config, sandbox_data_handler,
                                                                     shell_helper, tf_working_dir)
            if tf_proc_executer.can_execute_run():
                ProviderHandler.initialize_provider(shell_helper)
                tf_proc_executer.init_terraform()
                tf_proc_executer.tag_terraform()
                tf_proc_executer.plan_terraform()
                tf_proc_executer.apply_terraform()
                tf_proc_executer.save_terraform_outputs()
            else:
                self._handle_error_output(shell_helper, "This Terraform Module has been successfully deployed but "
                                                        "destroy failed. Please destroy successfully before running "
                                                        "execute again.")
        finally:
            if self._using_remote_state(shell_helper):
                LocalDir.delete_local_temp_dir(sandbox_data_handler, tf_working_dir)

    def destroy_terraform(self):
        # initialize a logger if logger wasn't passed during init
        with nullcontext(self._logger) if self._logger else LoggingSessionContext(self._context) as logger:

            shell_helper = ObjectFactory.create_shell_helper(self._tf_service, self._context, self._config, logger)
            sandbox_data_handler = SandboxDataHandler(shell_helper)
            self._validate_remote_backend_or_existing_working_dir(sandbox_data_handler, shell_helper)

            tf_working_dir = LocalDir.prepare_tf_working_dir(logger, sandbox_data_handler, shell_helper)
            self._destroy_procedure(sandbox_data_handler, shell_helper, tf_working_dir)

    def _destroy_procedure(self, sandbox_data_handler: SandboxDataHandler, shell_helper: ShellHelperObject,
                           tf_working_dir: str):
        if not tf_working_dir:
            self._handle_error_output(shell_helper, "Destroy failed due to missing local directory")

        try:
            ProviderHandler.initialize_provider(shell_helper)
            tf_proc_executer = ObjectFactory.create_tf_proc_executer(self._config, sandbox_data_handler,
                                                                     shell_helper, tf_working_dir)
            if tf_proc_executer.can_destroy_run():
                tf_proc_executer.init_terraform()
                tf_proc_executer.destroy_terraform()
            else:
                self._handle_error_output(shell_helper, "Destroy blocked because APPLY was not yet executed")
        finally:
            if self._using_remote_state(shell_helper) or self._destroy_passed(sandbox_data_handler):
                LocalDir.delete_local_temp_dir(sandbox_data_handler, tf_working_dir)

    def _validate_remote_backend_or_existing_working_dir(self, sandbox_data_handler, shell_helper):
        if not shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER) and \
                not LocalDir.does_working_dir_exists(sandbox_data_handler.get_tf_working_dir()):
            self._handle_error_output(shell_helper, f"Missing local folder {sandbox_data_handler.get_tf_working_dir()}")

    @staticmethod
    def _destroy_passed(sandbox_data_handler):
        return sandbox_data_handler.get_status(DESTROY_STATUS) == DESTROY_PASSED

    @staticmethod
    def _using_remote_state(shell_helper) -> bool:
        return bool(shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER))

    @staticmethod
    def _handle_error_output(shell_helper: ShellHelperObject, err_msg: str):
        shell_helper.sandbox_messages.write_error_message(err_msg)
        raise Exception(err_msg)
