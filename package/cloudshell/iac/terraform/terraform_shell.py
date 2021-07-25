import logging
import os
import shutil
import stat
import tempfile
from contextlib import nullcontext
from pathlib import Path

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
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler
from cloudshell.iac.terraform.services.tf_proc_exec import TfProcExec
from cloudshell.iac.terraform.models.tf_service import TerraformServiceObject
from cloudshell.iac.terraform.tagging.tags import TagsManager


class TerraformShell:
    # todo: add support to provide the info needed from attributes as parameters to the init (not shell attributes)
    def __init__(self, driver_context: ResourceCommandContext,
                 logger: logging.Logger = None, config: TerraformShellConfig = None):
        self._context = driver_context
        self._tf_service = self._create_tf_service()
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
                tf_proc_executer.tag_terraform()
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

            shell_helper = self._create_shell_helper(logger)
            sandbox_data_handler = SandboxDataHandler(shell_helper)
            tf_working_dir = sandbox_data_handler.get_tf_working_dir()

            if tf_working_dir:
                ProviderHandler.initialize_provider(shell_helper)
                tf_proc_executer = TfProcExec(shell_helper, sandbox_data_handler, InputOutputService(shell_helper))

                if tf_proc_executer.can_destroy_run():
                    tf_proc_executer.destroy_terraform()

                    tf_path = Path(tf_working_dir)
                    tmp_folder_found = False
                    while not tmp_folder_found:
                        objects_in_folder = os.listdir(tf_path.parent.absolute())
                        if len(objects_in_folder) == 2:
                            if objects_in_folder[0] == 'REPO' and objects_in_folder[1] == 'repo.zip':
                                tmp_folder_found = True
                        tf_path = Path(tf_path.parent.absolute())
                    tf_path_str = str(tf_path)
                    shutil.rmtree(tf_path_str)

                    sandbox_data_handler.set_tf_working_dir("")

                else:
                    raise Exception("Destroy blocked because APPLY was not yet executed")
            else:
                raise Exception("Destroy failed due to missing local directory")

    def _create_shell_helper(self, logger: logging.Logger) -> ShellHelperObject:
        api = CloudShellSessionContext(self._context).get_api()
        sandbox_id = self._context.reservation.reservation_id
        sandbox_message_service = SandboxMessagesService(api, sandbox_id, self._tf_service.name,
                                                         self._config.write_sandbox_messages)
        live_status_updater = LiveStatusUpdater(api, sandbox_id, self._config.update_live_status)
        default_tags = TagsManager(self._context.reservation)
        attr_handler = ServiceAttrHandler(self._tf_service)


        return ShellHelperObject(api, sandbox_id, self._tf_service, logger, sandbox_message_service,
                                 live_status_updater, attr_handler, default_tags)

    def _create_tf_service(self) -> TerraformServiceObject:
        api = CloudShellSessionContext(self._context).get_api()
        reservation_id = self._context.reservation.reservation_id
        cloudshell_model_name = self._context.resource.model
        name = self._context.resource.name

        return TerraformServiceObject(api, reservation_id, name, cloudshell_model_name)

    def _does_working_dir_exists(self, dir: str) -> bool:
        return dir and os.path.isdir(dir)