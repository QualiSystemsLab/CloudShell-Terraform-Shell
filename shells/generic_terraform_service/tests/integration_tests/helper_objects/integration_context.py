from unittest import mock
from unittest.mock import Mock

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.iac.terraform import TerraformShell, TerraformShellConfig
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext

from tests.integration_tests.helper_objects.env_vars import EnvVars
from tests.integration_tests.helper_services.service_attributes_factory import ServiceAttributesFactory


class IntegrationData(object):
    def __init__(self, service_name: str, is_api_real: bool = True, mock_api: Mock = None):
        #
        self._sb_service_alias = service_name

        if is_api_real:
            self._env_vars = EnvVars()
            self.api = CloudShellAPISession(
                self._env_vars.cs_server,
                self._env_vars.cs_user,
                self._env_vars.cs_pass,
                self._env_vars.cs_domain
            )

        else:
            self.api = mock_api
            self.api.authentication.xmlrpc_token = Mock()
        self._set_context(is_api_real)
        self._logger = get_qs_logger(log_group=self.context.resource.name)
        self.create_tf_shell()

    def _set_context(self, is_api_real: bool):
        self.context = mock.create_autospec(ResourceCommandContext)
        self.context.connectivity = mock.MagicMock()
        if is_api_real:
            self.context.connectivity.server_address = self._env_vars.cs_server
            self.context.connectivity.admin_auth_token = self.api.authentication.xmlrpc_token

        self.context.resource = mock.MagicMock()
        self.context.resource.attributes = dict()
        self.context.resource.name = self._sb_service_alias
        self.context.resource.model = 'Generic Terraform Service'
        if is_api_real:
            self.set_context_resource_attributes_from_cs()
            self.context.reservation = mock.MagicMock()
            self.context.reservation.reservation_id = self._env_vars.cs_res_id
            self.context.reservation.domain = self._env_vars.cs_domain
        else:
            self.context.resource.attributes = ServiceAttributesFactory.create_empty_attributes()
            self.context.reservation = mock.MagicMock()

    def set_context_resource_attributes_from_cs(self, the_only_attribute_to_update: str = ""):
        services = self.api.GetReservationDetails(self._env_vars.cs_res_id, disableCache=True) \
            .ReservationDescription.Services
        for service in services:
            if service.Alias == self._sb_service_alias:
                for attribute in service.Attributes:
                    if the_only_attribute_to_update and attribute.Name == the_only_attribute_to_update:
                        self.context.resource.attributes[attribute.Name] = attribute.Value
                        return
                    elif not the_only_attribute_to_update:
                        self.context.resource.attributes[attribute.Name] = attribute.Value

    def create_tf_shell(self):
        self._config = TerraformShellConfig(write_sandbox_messages=True, update_live_status=True)
        self.tf_shell = TerraformShell(self.context, self._logger, self._config)
