from logging import Logger

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig

from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from cloudshell.iac.terraform.tagging.tags import TagsManager


class CPShellHelperObject:
    def __init__(
        self,
        resource_config: TerraformResourceConfig,
        res_id: str,
        logger: Logger,
        sandbox_messages: SandboxMessagesService,
        live_status_updater: LiveStatusUpdater,
        # attr_handler: ServiceAttrHandler,
        default_tags: TagsManager,
    ):
        self.api = resource_config.api
        self.sandbox_id = res_id
        self.logger = logger
        self.sandbox_messages = sandbox_messages
        self.live_status_updater = live_status_updater
        self.attr_handler = resource_config
        self.default_tags = default_tags
