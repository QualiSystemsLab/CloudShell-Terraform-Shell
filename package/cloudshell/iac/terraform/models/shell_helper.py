from logging import Logger

from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler


class ShellHelperObject(object):

    def __init__(self, api: CloudShellAPISession, res_id: str, tf_service: any, logger: Logger,
                 sandbox_messages: SandboxMessagesService, live_status_updater: LiveStatusUpdater):
        self.api = api
        self.sandbox_id = res_id
        self.tf_service = tf_service
        self.logger = logger
        self.sandbox_messages = sandbox_messages
        self.live_status_updater = live_status_updater

        self.attr_handler = ServiceAttrHandler(
            self.api,
            self.sandbox_id,
            self.tf_service
        )
