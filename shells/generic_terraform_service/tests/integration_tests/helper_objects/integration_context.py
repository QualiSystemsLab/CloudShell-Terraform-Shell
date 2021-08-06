from unittest import mock
from unittest.mock import Mock

from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeValueInfo
from cloudshell.iac.terraform import TerraformShell, TerraformShellConfig
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext

from tests.integration_tests.helper_objects.env_vars import EnvVars


class IntegrationData(object):
    def __init__(self, service_name: str, real_api: bool = True, mocked_attributes: list[AttributeValueInfo] = None):
        self._env_vars = EnvVars(service_name)

        if real_api:
            self.api = CloudShellAPISession(
                self._env_vars.cs_server,
                self._env_vars.cs_user,
                self._env_vars.cs_pass,
                self._env_vars.cs_domain
            )
            self._set_context(real_api)
            self._logger = get_qs_logger(log_group=self.context.resource.name)
            self.create_tf_shell()

        else:
            self.api = Mock()
            self.api.authentication.xmlrpc_token = Mock()
            self._set_context(real_api)
            self._logger = get_qs_logger(log_group=self.context.resource.name)

            self._set_context(real_api, mocked_attributes)

    def _set_context(self, real_api: bool, mocked_attributes: list[AttributeValueInfo] = None):
        self.context = mock.create_autospec(ResourceCommandContext)
        self.context.connectivity = mock.MagicMock()
        self.context.connectivity.server_address = self._env_vars.cs_server
        self.context.connectivity.admin_auth_token = self.api.authentication.xmlrpc_token

        self.context.resource = mock.MagicMock()
        self.context.resource.attributes = dict()
        self.context.resource.name = self._env_vars.sb_service_alias
        self.context.resource.model = 'Generic Terraform Service'
        if real_api:
            self.set_context_resource_attributes_from_cs()

        self.context.reservation = mock.MagicMock()
        self.context.reservation.reservation_id = self._env_vars.cs_res_id
        self.context.reservation.domain = self._env_vars.cs_domain

    def set_context_resource_attributes_from_cs(self, the_only_attribute_to_update: str = ""):
        services = self.api.GetReservationDetails(self._env_vars.cs_res_id, disableCache=True) \
            .ReservationDescription.Services
        for service in services:
            if service.Alias == self._env_vars.sb_service_alias:
                for attribute in service.Attributes:
                    if the_only_attribute_to_update and attribute.Name == the_only_attribute_to_update:
                        self.context.resource.attributes[attribute.Name] = attribute.Value
                        return
                    elif not the_only_attribute_to_update:
                        self.context.resource.attributes[attribute.Name] = attribute.Value

    def create_tf_shell(self):
        self._config = TerraformShellConfig(write_sandbox_messages=True, update_live_status=True)
        self.tf_shell = TerraformShell(self.context, self._logger, self._config)
