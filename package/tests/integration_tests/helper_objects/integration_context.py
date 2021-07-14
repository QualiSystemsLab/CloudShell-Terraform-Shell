import os
from unittest import mock
from unittest.mock import Mock

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext

from dotenv import load_dotenv

from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from tests.integration_tests.helper_objects.env_vars import EnvVars
from shells.generic_terraform_service.src.driver import GenericTerraformServiceDriver


class IntegrationData(object):
    def __init__(self):
        self._env_vars = EnvVars()
        self.real_api = CloudShellAPISession(
            self._env_vars.cs_server,
            self._env_vars.cs_user,
            self._env_vars.cs_pass,
            self._env_vars.cs_domain
        )
        self._set_context()
        self.logger = get_qs_logger(log_group=self.context.resource.name)

        self.sandbox_messages = SandboxMessagesService(
            self.real_api,
            self.context.reservation.reservation_id,
            self.context.resource.name,
            True,
        )

        self.live_status_updater = LiveStatusUpdater(
            self.real_api,
            self.context.reservation.reservation_id,
            True
        )

        # service_resource = GenericTerraformService.create_from_context(self.context)
        service_resource = Mock()
        load_dotenv()
        service_resource.github_token = os.environ.get("GITHUB_TOKEN_ENC")

        self.driver_helper = ShellHelperObject(
            self.real_api,
            self.context.reservation.reservation_id,
            service_resource,
            self.logger,
            self.sandbox_messages,
            self.live_status_updater
        )

        self._create_driver()

    def _set_context(self):
        self.context = mock.create_autospec(ResourceCommandContext)
        self.context.connectivity = mock.MagicMock()
        self.context.connectivity.server_address = self._env_vars.cs_server
        self.context.connectivity.admin_auth_token = self.real_api.authentication.xmlrpc_token

        self.context.resource = mock.MagicMock()
        self.context.resource.attributes = dict()
        self.context.resource.name = self._env_vars.sb_service_alias
        self.set_context_resource_attributes()

        self.context.reservation = mock.MagicMock()
        self.context.reservation.reservation_id = self._env_vars.cs_res_id
        self.context.reservation.domain = self._env_vars.cs_domain

    def set_context_resource_attributes(self):
        services = self.real_api.GetReservationDetails(self._env_vars.cs_res_id).ReservationDescription.Services
        for service in services:
            if service.Alias == self._env_vars.sb_service_alias:
                for attribute in service.Attributes:
                    self.context.resource.attributes[attribute.Name] = attribute.Value

    def _create_driver(self) :
      self.driver = GenericTerraformServiceDriver()
      self.driver.initialize(self.context)