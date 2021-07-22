import mock
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext


from tests.integration_tests.helper_objects.env_vars import EnvVars

from driver import AzureTfBackendDriver


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
        self._logger = get_qs_logger(log_group=self.context.resource.name)

        self._create_driver()

    def _set_context(self):
        self.context = mock.create_autospec(ResourceCommandContext)
        self.context.connectivity = mock.MagicMock()
        self.context.connectivity.server_address = self._env_vars.cs_server
        self.context.connectivity.admin_auth_token = self.real_api.authentication.xmlrpc_token

        self.context.resource = mock.MagicMock()
        self.context.resource.attributes = dict()
        self.context.resource.name = self._env_vars.cs_resource
        self.set_context_resource_attributes()

        self.context.reservation = mock.MagicMock()
        self.context.reservation.reservation_id = self._env_vars.cs_res_id
        self.context.reservation.domain = self._env_vars.cs_domain

    def set_context_resource_attributes(self):
        for attribute in self.real_api.GetResourceDetails(self._env_vars.cs_resource).ResourceAttributes:
            self.context.resource.attributes[attribute.Name] = attribute.Value

    def _create_driver(self):
        self.driver = AzureTfBackendDriver()
        self.driver.initialize(self.context)
