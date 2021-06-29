import os
from unittest import mock, TestCase
from unittest.mock import Mock, patch
from cloudshell.api.cloudshell_api import CloudShellAPISession


from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext

from constants import SHELL_NAME, GITHUB_TF_FOLDER_LINK
from data_model import TerraformService2G
from driver import TerraformService2GDriver
from driver_helper_obj import DriverHelperObject
from tests.test_constants import CS_SERVER, CS_USERNAME, CS_PASSWORD, RESERVATION_ID, RESERVATION_DOMAIN, CLP_RESOURSE, \
    TFEXEC_VERSION
from tests.test_driver import _DecryptPassword

class RealDebugInstance(TestCase):
    def setUp(self) -> None:
        self._real_api = CloudShellAPISession(CS_SERVER, CS_USERNAME, CS_PASSWORD, "Global")

        self._context = self._prepare_context()
        self._driver = self._create_driver()

        mock_api = Mock()

        mock_api.GetSandboxData = self._real_api.GetSandboxData
        mock_api.SetSandboxData = self._real_api.SetSandboxData
        mock_api.ClearSandboxData = self._real_api.ClearSandboxData

        mock_api.DecryptPassword = _DecryptPassword
        mock_api.GetSandboxData = self._real_api.GetSandboxData
        mock_api.SetSandboxData = self._real_api.SetSandboxData
        mock_api.ClearSandboxData = self._real_api.ClearSandboxData
        mock_api.GetResourceDetails = self._real_api.GetResourceDetails

        mock_resource_details = Mock()
        mock_resource_details.ResourceModelName = "Microsoft Azure"
        mock_resource_details.ResourceFamilyName = "Cloud Provider"

        api = mock_api
        res_id = self._context.reservation.reservation_id
        service_resource = TerraformService2G.create_from_context(self._context)
        logger = get_qs_logger(log_group=self._context.resource.name)
        self._driver_helper_object = DriverHelperObject(api, res_id, service_resource, logger)


    def _prepare_context(self):
        context = mock.create_autospec(ResourceCommandContext)

        context.connectivity = mock.MagicMock()

        # token = api.authentication.xmlrpc_token
        context.connectivity.server_address = CS_SERVER
        context.connectivity.admin_auth_token = self._real_api.authentication.xmlrpc_token

        context.resource = mock.MagicMock()
        context.resource.attributes = dict()
        context.resource.name = 'ooo'

        context.resource.attributes[f"{SHELL_NAME}.Github Terraform Module URL"] = GITHUB_TF_FOLDER_LINK
        gh_token = os.environ['GH_TOKEN']
        context.reservation = mock.MagicMock()
        context.reservation.reservation_id = RESERVATION_ID
        context.reservation.domain = RESERVATION_DOMAIN
        context.resource.attributes[f"{SHELL_NAME}.Github Token"] = gh_token
        context.resource.attributes[f"{SHELL_NAME}.Cloud Provider"] = CLP_RESOURSE
        context.resource.attributes[f"{SHELL_NAME}.Terraform Version"] = TFEXEC_VERSION
        context.resource.attributes[f"{SHELL_NAME}.Terraform Working Dir"] = ""
        context.resource.attributes[f"{SHELL_NAME}.UUID"] = ""

        return context

    def _create_driver(self) -> TerraformService2GDriver:
        driver = TerraformService2GDriver()
        driver.initialize(self._context)
        return driver

    @patch("driver.CloudShellSessionContext")
    def test_test1(self, cssc):
        self._context.resource.attributes[
            f"{SHELL_NAME}.Terraform Inputs"] = "KEYVAULT_NAME=alexaz-amd-test,KEYVAULT_RG=alexaz-test-amd,SECRET_NAME=test"
        cssc.return_value.get_api.return_value = self._real_api

        self._real_api.ClearSandboxData(self._driver_helper_object.res_id)
        # cssc.return_value.get_api.return_value = self._driver_helper_object.api

        services = self._real_api.GetReservationDetails(RESERVATION_ID).ReservationDescription.Services
        for attribute in services[0].Attributes:
            if attribute.Name == 'Terraform Service 2G.Github Token':
                self._context.resource.attributes[f"{SHELL_NAME}.Github Token"] = attribute.Value

        self._driver.execute_terraform(self._context)
        services = self._real_api.GetReservationDetails(RESERVATION_ID).ReservationDescription.Services
        for attribute in services[0].Attributes:
            if attribute.Name == f"{SHELL_NAME}.Terraform Working Dir":
                self._context.resource.attributes[f"{SHELL_NAME}.Terraform Working Dir"] = attribute.Value
            if attribute.Name == f"{SHELL_NAME}.UUID":
                self._context.resource.attributes[f"{SHELL_NAME}.UUID"] = attribute.Value
        data = self._real_api.GetSandboxData(self._driver_helper_object.res_id)
        self._driver.destroy_terraform(self._context)
