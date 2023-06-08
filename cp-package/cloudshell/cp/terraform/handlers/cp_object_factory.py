import logging

from cloudshell.iac.terraform import TerraformShellConfig
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.models.tf_service import TerraformServiceObject
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.object_factory import ObjectFactory
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler
from cloudshell.iac.terraform.tagging.tags import TagsManager
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.cp.terraform.models.cp_shell_helper import CPShellHelperObject
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


class CPObjectFactory:
    @staticmethod
    def create_tf_proc_executer(
        config: TerraformResourceConfig,
        sandbox_data_handler: SandboxDataHandler,
        shell_helper: ShellHelperObject,
        tf_working_dir: str,
    ) -> TfProcExec:
        backend_handler = BackendHandler(
            shell_helper, tf_working_dir, sandbox_data_handler.get_tf_uuid()
        )
        input_output_service = InputOutputService(
            shell_helper, config.inputs_map, config.outputs_map
        )
        tf_proc_executer = TfProcExec(
            shell_helper, sandbox_data_handler, backend_handler, input_output_service
        )
        return tf_proc_executer

    @staticmethod
    def create_shell_helper(
        resource_config: TerraformResourceConfig,
        sandbox_id: str,
        tag_manager: TagsManager,
        config: TerraformShellConfig,
        logger: logging.Logger,
    ) -> CPShellHelperObject:
        api = resource_config.api
        sandbox_message_service = SandboxMessagesService(
            api, sandbox_id, resource_config.name, config.write_sandbox_messages
        )
        live_status_updater = LiveStatusUpdater(
            api, sandbox_id, config.update_live_status
        )
        default_tags = tag_manager

        return CPShellHelperObject(
            api=api,
            res_id=sandbox_id,
            resource_config=resource_config,
            logger=logger,
            sandbox_messages=sandbox_message_service,
            live_status_updater=live_status_updater,
            default_tags=default_tags,
        )
