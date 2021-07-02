import time
from unittest import mock

from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeNameValue
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext

from data_model import TerraformService2G
from driver import TerraformService2GDriver
from driver_helper_obj import DriverHelperObject
from tests.constants import SHELL_NAME
from tests.integration_tests.helpers.env_vars import EnvVars


class IntegrationTestsData(object):
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

        service_resource = TerraformService2G.create_from_context(self.context)
        self.driver_helper = DriverHelperObject(
            self.real_api,
            self.context.reservation.reservation_id,
            service_resource,
            self._logger
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

    def _create_driver(self):
        self.driver = TerraformService2GDriver()
        self.driver.initialize(self.context)

    def set_attribute(self, attribute_name: str, attribute_value: str = ""):
        attributes_list = [AttributeNameValue(f"{SHELL_NAME}.{attribute_name}", attribute_value)]
        self.real_api.SetServiceAttributesValues(self.driver_helper.res_id,
                                                 self.driver_helper.tf_service.name,
                                                 attributes_list)
        self.context.resource.attributes[f"{SHELL_NAME}.{attribute_name}"] = attribute_value

    def get_attribute(self, attribute_name: str) -> str:
        services = self.real_api.GetReservationDetails(self.driver_helper.res_id, disableCache=True).ReservationDescription.Services
        for service in services:
            if service.Alias == self._env_vars.sb_service_alias:
                for attribute in service.Attributes:
                    if attribute.Name == f"{SHELL_NAME}.{attribute_name}":
                        return attribute.Value
        return ""
