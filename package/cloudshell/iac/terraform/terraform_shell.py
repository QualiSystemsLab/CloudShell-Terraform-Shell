import logging
import os
from contextlib import nullcontext

from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.iac.terraform import TerraformShellConfig
from cloudshell.iac.terraform.constants import DESTROY_STATUS, DESTROY_PASSED, ATTRIBUTE_NAMES, DESTROY_FAILED
from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.backend_handler import BackendHandler
from cloudshell.iac.terraform.services.input_output_service import InputOutputService
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.local_dir_handler import delete_local_temp_dir
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
            tf_working_dir = self._prepare_tf_working_dir(logger, sandbox_data_handler, shell_helper)
            tf_proc_executer = self._create_tf_proc_executer(sandbox_data_handler, shell_helper, tf_working_dir)

            if tf_proc_executer.can_execute_run():
                self._execute_procedure(sandbox_data_handler, shell_helper, tf_proc_executer, tf_working_dir)
            else:
                err_msg = "Execution is not enabled due to either failed previous Execution (*Try Destroy first) or " \
                          "Successfully executed previously without successfully destroying it first"
                shell_helper.sandbox_messages.write_message(err_msg)
                raise Exception(err_msg)

    def _execute_procedure(self, sandbox_data_handler, shell_helper, tf_proc_executer, tf_working_dir):
        ProviderHandler.initialize_provider(shell_helper)
        tf_proc_executer.init_terraform()
        tf_proc_executer.tag_terraform()
        tf_proc_executer.plan_terraform()
        tf_proc_executer.apply_terraform()
        tf_proc_executer.save_terraform_outputs()
        if self._using_remote_state(shell_helper):
            delete_local_temp_dir(sandbox_data_handler, tf_working_dir)

    def destroy_terraform(self):
        # initialize a logger if logger wasn't passed during init
        with nullcontext(self._logger) if self._logger else LoggingSessionContext(self._context) as logger:

            shell_helper = self._create_shell_helper(logger)
            sandbox_data_handler = SandboxDataHandler(shell_helper)
            self._validate_remote_backend_or_existing_working_dir(sandbox_data_handler, shell_helper)

            tf_working_dir = self._prepare_tf_working_dir(logger, sandbox_data_handler, shell_helper)

            if tf_working_dir:
                ProviderHandler.initialize_provider(shell_helper)
                tf_proc_executer = self._create_tf_proc_executer(sandbox_data_handler, shell_helper, tf_working_dir)
                if tf_proc_executer.can_destroy_run():
                    self._destroy_procedure(sandbox_data_handler, shell_helper, tf_proc_executer, tf_working_dir)
                else:
                    raise Exception("Destroy blocked because APPLY was not yet executed")
            else:
                raise Exception("Destroy failed due to missing local directory")

    def _destroy_procedure(self, sandbox_data_handler, shell_helper, tf_proc_executer, tf_working_dir):
        tf_proc_executer.init_terraform()
        tf_proc_executer.destroy_terraform()
        if self._using_remote_state(shell_helper) or self._destroy_passed(sandbox_data_handler):
            delete_local_temp_dir(sandbox_data_handler, tf_working_dir)

    def _validate_remote_backend_or_existing_working_dir(self, sandbox_data_handler, shell_helper):
        if not shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER) and \
                not self._does_working_dir_exists(sandbox_data_handler.get_tf_working_dir()):
            raise ValueError(f"Missing local folder {sandbox_data_handler.get_tf_working_dir()}")

    def _prepare_tf_working_dir(self, logger, sandbox_data_handler, shell_helper):
        tf_working_dir = sandbox_data_handler.get_tf_working_dir()
        if not self._does_working_dir_exists(tf_working_dir):
            # working dir doesnt exist - need to download repo and tf exec
            downloader = Downloader(shell_helper)
            tf_working_dir = downloader.download_terraform_module()

            downloader.download_terraform_executable(tf_working_dir)
            sandbox_data_handler.set_tf_working_dir(tf_working_dir)
        else:
            logger.info(f"Using existing working dir = {tf_working_dir}")
        return tf_working_dir

    def _destroy_passed(self, sandbox_data_handler):
        return sandbox_data_handler.get_status(DESTROY_STATUS) == DESTROY_PASSED

    def _using_remote_state(self, shell_helper) -> bool:
        return bool(shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER))

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

    def _create_tf_proc_executer(self, sandbox_data_handler, shell_helper, tf_working_dir):
        backend_handler = BackendHandler(shell_helper, tf_working_dir, sandbox_data_handler.get_tf_uuid())
        input_output_service = InputOutputService(shell_helper, self._config.inputs_map, self._config.outputs_map)
        tf_proc_executer = TfProcExec(shell_helper, sandbox_data_handler, backend_handler, input_output_service)
        return tf_proc_executer