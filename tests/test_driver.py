import os
from unittest import mock, TestCase
from unittest.mock import Mock, patch
from subprocess import Popen, PIPE

from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext


from data_model import TerraformService2G
from downloaders.downloader import Downloader
from driver import TerraformService2GDriver
from driver_helper_obj import DriverHelperObject
from constants import CS_SERVER, CS_USERNAME, CS_PASSWORD, RESERVATION_ID, RESERVATION_DOMAIN, CLP_RESOURSE, \
    TFEXEC_VERSION, SHELL_NAME, GITHUB_TF_FOLDER_LINK, TERRAFORM_FILE, TERRAFORM_EXEC_FILE
from services.provider_handler import ProviderHandler


class MainDriverTest(TestCase):
    def setUp(self) -> None:

        self._context = self._prepare_context()
        self._driver = self._create_driver()
        # api = CloudShellSessionContext(self._context).get_api()
        mock_api = Mock()
        mock_api.DecryptPassword = _DecryptPassword

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
        # self._init_terraform = driver.TerraformService2GDriver._init_terraform

    def _prepare_context(self):

        context = mock.create_autospec(ResourceCommandContext)

        context.connectivity = mock.MagicMock()
        # api = CloudShellAPISession(CS_SERVER, CS_USERNAME, CS_PASSWORD, "Global")
        # token = api.authentication.xmlrpc_token
        context.connectivity.server_address = CS_SERVER
        # context.connectivity.admin_auth_token = token

        context.resource = mock.MagicMock()
        context.resource.attributes = dict()
        context.resource.name = "service_test"

        context.resource.attributes[f"{SHELL_NAME}.Github Terraform Module URL"] = GITHUB_TF_FOLDER_LINK
        gh_token = os.environ['GH_TOKEN']
        context.reservation = mock.MagicMock()
        context.reservation.reservation_id = RESERVATION_ID
        context.reservation.domain = RESERVATION_DOMAIN
        context.resource.attributes[f"{SHELL_NAME}.Github Token"] = gh_token
        context.resource.attributes[f"{SHELL_NAME}.Cloud Provider"] = CLP_RESOURSE
        context.resource.attributes[f"{SHELL_NAME}.Terraform Version"] = TFEXEC_VERSION
        return context

    def _create_driver(self) -> TerraformService2GDriver:
        driver = TerraformService2GDriver()
        driver.initialize(self._context)
        return driver

    def test_download_terraform_module(self):
        downloader = Downloader(self._driver_helper_object)
        tf_workingdir = downloader.download_terraform_module()
        self.assertTrue(os.path.exists(os.path.join(tf_workingdir,TERRAFORM_FILE)))

    def test_download_terraform_executable(self):
        downloader = Downloader(self._driver_helper_object)
        tf_workingdir = downloader.download_terraform_module()
        downloader.download_terraform_executable(tf_workingdir)

        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE)))
        self.assertTrue(os.access(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE), os.X_OK))

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
        self.assertEqual(self._driver_helper_object.api.SetServiceAttributesValues.call_args.args[2][0].Name,
                    'Terraform Service 2G.Terraform Output')
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



def _DecryptPassword(x):
    result = mock.MagicMock()
    result.Value = x
    return result