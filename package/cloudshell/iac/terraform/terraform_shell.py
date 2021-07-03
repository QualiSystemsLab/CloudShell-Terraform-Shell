import logging
from contextlib import nullcontext

from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.input_output_service import InputOutputService
from cloudshell.iac.terraform.services.provider_handler import ProviderHandler
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler
from cloudshell.iac.terraform.services.tf_proc_exec import TfProcExec


class TerraformShell:
    def __init__(self, driver_context: ResourceCommandContext, terraform_service_shell: any, logger: logging.Logger):
        self._context = driver_context
        self._tf_service = terraform_service_shell
        self._logger = logger

    def execute_terraform(self):
        # initialize a logger if logger wasn't passed during init
        with nullcontext(self._logger) if self._logger else LoggingSessionContext(self._context) as logger:

            shell_model = self._create_shell_helper(logger)

            downloader = Downloader(shell_model)
            tf_workingdir = downloader.download_terraform_module()
            downloader.download_terraform_executable(tf_workingdir)

            tf_proc_executer = TfProcExec(shell_model,
                                          SandboxDataHandler(shell_model, tf_workingdir),
                                          InputOutputService(shell_model))
            if tf_proc_executer.can_execute_run():
                ProviderHandler.initialize_provider(shell_model)
                tf_proc_executer.init_terraform()
                tf_proc_executer.plan_terraform()
                tf_proc_executer.apply_terraform()
                tf_proc_executer.save_terraform_outputs()
            else:
                err_msg = "Execution is not enabled due to either failed previous Execution (*Try Destroy first) or " \
                          "Successfully executed previously without successfully destroying it first"
                shell_model.api.WriteMessageToReservationOutput(shell_model.sandbox_id, err_msg)
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
                raise Exception("Destroy blocked due to missing state file")

    def _create_shell_helper(self, logger: logging.Logger) -> ShellHelperObject:
        api = CloudShellSessionContext(self._context).get_api()
        sandbox_id = self._context.reservation.reservation_id
        return ShellHelperObject(api, sandbox_id, self._tf_service, logger)
