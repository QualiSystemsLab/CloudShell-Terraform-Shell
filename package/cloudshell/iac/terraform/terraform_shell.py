import logging
import os
from contextlib import nullcontext

from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.iac.terraform import TerraformShellConfig
from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.input_output_service import InputOutputService
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.provider_handler import ProviderHandler
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler
from cloudshell.iac.terraform.services.tf_proc_exec import TfProcExec


class TerraformShell:
    # todo: add support to provide the info needed from attributes as parameters to the init (not shell attributes)
    def __init__(self, driver_context: ResourceCommandContext, terraform_service_shell: any,
                 logger: logging.Logger = None, config: TerraformShellConfig = None):
        self._context = driver_context
        self._tf_service = terraform_service_shell
        self._logger = logger
        self._config = config or TerraformShellConfig()

    def execute_terraform(self):
        # initialize a logger if logger wasn't passed during init
        with nullcontext(self._logger) if self._logger else LoggingSessionContext(self._context) as logger:

            shell_helper = self._create_shell_helper(logger)
            sandbox_data_handler = SandboxDataHandler(shell_helper)
            tf_working_dir = sandbox_data_handler.get_tf_working_dir()

            if not self._does_working_dir_exists(tf_working_dir):
                # working dir doesnt exist - need to download repo and tf exec
                downloader = Downloader(shell_helper)
                tf_workingdir = downloader.download_terraform_module()
                downloader.download_terraform_executable(tf_workingdir)
                sandbox_data_handler.set_tf_working_dir(tf_workingdir)
            else:
                logger.info(f"Using existing working dir = {tf_working_dir}")

            tf_proc_executer = TfProcExec(shell_helper,
                                          sandbox_data_handler,
                                          InputOutputService(shell_helper))
            if tf_proc_executer.can_execute_run():
                ProviderHandler.initialize_provider(shell_helper)
                tf_proc_executer.init_terraform()
                tf_proc_executer.plan_terraform()
                tf_proc_executer.apply_terraform()
                tf_proc_executer.save_terraform_outputs()
            else:
                err_msg = "Execution is not enabled due to either failed previous Execution (*Try Destroy first) or " \
                          "Successfully executed previously without successfully destroying it first"
                shell_helper.sandbox_messages.write_message(err_msg)
                raise Exception(err_msg)

    def destroy_terraform(self):
        # initialize a logger if logger wasn't passed during init
        with nullcontext(self._logger) if self._logger else LoggingSessionContext(self._context) as logger:

            shell_model = self._create_shell_helper(logger)
            sandbox_data_handler = SandboxDataHandler(shell_model)

            if sandbox_data_handler.get_tf_working_dir():
                ProviderHandler.initialize_provider(shell_model)
                tf_proc_executer = TfProcExec(shell_model, sandbox_data_handler, InputOutputService(shell_model))
                if tf_proc_executer.can_destroy_run():
                    tf_proc_executer.destroy_terraform()
                else:
                    raise Exception("Destroy blocked because APPLY was not yet executed")
            else:
                raise Exception("Destroy failed due to missing state file")

    def _create_shell_helper(self, logger: logging.Logger) -> ShellHelperObject:
        api = CloudShellSessionContext(self._context).get_api()
        sandbox_id = self._context.reservation.reservation_id
        sandbox_message_service = SandboxMessagesService(api, sandbox_id, self._tf_service.name,
                                                         self._config.write_sandbox_messages)
        live_status_updater = LiveStatusUpdater(api, sandbox_id, self._config.update_live_status)

        return ShellHelperObject(api, sandbox_id, self._tf_service, logger, sandbox_message_service,
                                 live_status_updater)

    def _does_working_dir_exists(self, dir: str) -> bool:
        return dir and os.path.isdir(dir)
