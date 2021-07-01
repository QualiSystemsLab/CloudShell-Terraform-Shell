import os
from typing import List
from unittest import mock, TestCase
from unittest.mock import Mock, patch
from subprocess import Popen, PIPE

from cloudshell.api.cloudshell_api import SandboxDataKeyValue
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext

from data_model import TerraformService2G
from driver import TerraformService2GDriver
from driver_helper_obj import DriverHelperObject
from tests.test_constants import SHELL_NAME
from services.provider_handler import ProviderHandler
from dotenv import load_dotenv
load_dotenv()


class MainDriverTest(TestCase):
    def setUp(self) -> None:
        # used to mock sandbox data
        self._sdkv_list = []

        self._context = self._prepare_context()
        self._driver = self._create_driver()

        mock_api = Mock()

        mock_api.DecryptPassword = _decrypt_password
        mock_api.GetSandboxData = self._get_sb_data
        mock_api.SetSandboxData = self._set_sb_data

        mock_resource_details = Mock()
        mock_resource_details.ResourceModelName = "Microsoft Azure"
        mock_resource_details.ResourceFamilyName = "Cloud Provider"

        mock_api.GetResourceDetails.return_value = mock_resource_details

        mock_resource_attributes = [Mock(Name="Azure Subscription ID", Value="ARM_SUBSCRIPTION_ID_MOCKVALUE"),
                                    Mock(Name="Azure Tenant ID", Value="ARM_TENANT_ID_MOCKVALUE"),
                                    Mock(Name="Azure Application ID", Value="ARM_CLIENT_ID_MOCKVALUE"),
                                    Mock(Name="Azure Application Key", Value="ARM_CLIENT_SECRET_MOCKVALUE")]

        mock_api.GetResourceDetails.return_value.ResourceAttributes = mock_resource_attributes

        api = mock_api
        res_id = self._context.reservation.reservation_id
        service_resource = TerraformService2G.create_from_context(self._context)
        logger = get_qs_logger(log_group=self._context.resource.name)
        self._driver_helper_object = DriverHelperObject(api, res_id, service_resource, logger)

    def _prepare_context(self):
        load_dotenv()
        context = mock.create_autospec(ResourceCommandContext)

        context.connectivity = mock.MagicMock()

        context.resource = mock.MagicMock()
        context.resource.attributes = dict()
        context.resource.name = "service_test"

        context.resource.attributes[f"{SHELL_NAME}.Github Terraform Module URL"] = \
            os.environ.get("GITHUB_TF_PRIVATE_HELLO_URL")

        # gh_token = os.environ['GH_TOKEN']
        context.reservation = mock.MagicMock()
        context.reservation.reservation_id = os.environ.get("RESERVATION_ID")
        context.reservation.domain = os.environ.get("RESERVATION_DOMAIN")
        context.resource.attributes[f"{SHELL_NAME}.Github Token"] = os.environ.get("GH_TOKEN")
        context.resource.attributes[f"{SHELL_NAME}.Cloud Provider"] = os.environ.get("CLP_RESOURCE")
        context.resource.attributes[f"{SHELL_NAME}.Terraform Version"] = os.environ.get("TFEXEC_VERSION")
        return context

    def _create_driver(self) -> TerraformService2GDriver:
        driver = TerraformService2GDriver()
        driver.initialize(self._context)
        return driver

    def test_initialize_provider(self):
        ProviderHandler.initialize_provider(self._driver_helper_object)

        self._validate_env_var("%ARM_SUBSCRIPTION_ID%", "ARM_SUBSCRIPTION_ID_MOCKVALUE")
        self._validate_env_var("%ARM_TENANT_ID%", "ARM_TENANT_ID_MOCKVALUE")
        self._validate_env_var("%ARM_CLIENT_ID%", "ARM_CLIENT_ID_MOCKVALUE")
        self._validate_env_var("%ARM_CLIENT_SECRET%", "ARM_CLIENT_SECRET_MOCKVALUE")

    def _validate_env_var(self, var, value):
        process = Popen(['echo', var], stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        print(f"var={var} output={stdout.decode('utf-8').rstrip()} value={value}")
        self.assertEqual(stdout.decode("utf-8").rstrip(), value)

    @patch("driver.CloudShellSessionContext")
    def test_execute_terraform_wout_input(self, cssc):
        # Arrange
        cssc.return_value.get_api.return_value = self._driver_helper_object.api

        # Act
        self._driver.execute_terraform(self._context)

        # Assert
        self.assertEqual(
            self._driver_helper_object.api.SetServiceAttributesValues.call_args.args[2][0].Name,
            'Terraform Service 2G.Terraform Output'
        )
        self.assertEqual(self._driver_helper_object.api.SetServiceAttributesValues.call_args.args[2][0].Value,
                         'hello=World!')

    @patch("driver.CloudShellSessionContext")
    def test_execute_terraform_with_input(self, cssc):
        # Arrange
        cssc.return_value.get_api.return_value = self._driver_helper_object.api

        self._context.resource.attributes[f"{SHELL_NAME}.Terraform Inputs"] = "hello=Test!"
        # Act
        self._driver.execute_terraform(self._context)

        # Assert
        self.assertEqual(self._driver_helper_object.api.SetServiceAttributesValues.call_args.args[2][0].Name,
                         'Terraform Service 2G.Terraform Output')
        self.assertEqual(self._driver_helper_object.api.SetServiceAttributesValues.call_args.args[2][0].Value,
                         'hello=Test!')

    def _set_sb_data(self, resid: str, sdkv_list=List[SandboxDataKeyValue]) -> None:
        self._sdkv_list = sdkv_list

    def _get_sb_data(self, resid: str):
        mock_sdb = Mock()
        mock_sdb.SandboxDataKeyValues = self._sdkv_list
        return mock_sdb


def _decrypt_password(x):
    result = mock.MagicMock()
    result.Value = x
    return result
