import logging

from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.iac.terraform import TerraformShellConfig
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.models.tf_service import TerraformServiceObject
from cloudshell.iac.terraform.services.backend_handler import BackendHandler
from cloudshell.iac.terraform.services.input_output_service import InputOutputService
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler
from cloudshell.iac.terraform.services.tf_proc_exec import TfProcExec
from cloudshell.iac.terraform.tagging.tags import TagsManager


class ObjectFactory:

    @staticmethod
    def create_tf_proc_executer(config: TerraformShellConfig,
                                sandbox_data_handler: SandboxDataHandler,
                                shell_helper: ShellHelperObject,
                                tf_working_dir: str) -> TfProcExec:
        backend_handler = BackendHandler(shell_helper, tf_working_dir, sandbox_data_handler.get_tf_uuid())
        input_output_service = InputOutputService(shell_helper, config.inputs_map, config.outputs_map)
        tf_proc_executer = TfProcExec(shell_helper, sandbox_data_handler, backend_handler, input_output_service)
        return tf_proc_executer

    @staticmethod
    def create_shell_helper(tf_service: TerraformServiceObject,
                            context: ResourceCommandContext,
                            config: TerraformShellConfig,
                            logger: logging.Logger) -> ShellHelperObject:
        api = CloudShellSessionContext(context).get_api()
        sandbox_id = context.reservation.reservation_id
        sandbox_message_service = SandboxMessagesService(api, sandbox_id, tf_service.name,
                                                         config.write_sandbox_messages)
        live_status_updater = LiveStatusUpdater(api, sandbox_id, config.update_live_status)
        default_tags = TagsManager(context.reservation)
        attr_handler = ServiceAttrHandler(tf_service)

        return ShellHelperObject(api, sandbox_id, tf_service, logger, sandbox_message_service,
                                 live_status_updater, attr_handler, default_tags)

    @staticmethod
    def create_tf_service(context: ResourceCommandContext) -> TerraformServiceObject:
        api = CloudShellSessionContext(context).get_api()
        reservation_id = context.reservation.reservation_id
        cloudshell_model_name = context.resource.model
        name = context.resource.name

        return TerraformServiceObject(api, reservation_id, name, cloudshell_model_name)
