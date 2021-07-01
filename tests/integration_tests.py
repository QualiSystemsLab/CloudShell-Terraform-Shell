import os
from unittest import mock, TestCase
from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext
from dotenv import load_dotenv

from data_model import TerraformService2G
from downloaders.downloader import Downloader
from driver import TerraformService2GDriver
from driver_helper_obj import DriverHelperObject
from tests.test_constants import TF_HELLO_FILE, TERRAFORM_EXEC_FILE, GITHUB_TF_PUBLIC_HELLO_URL, VAULT_TF_INPUTS, \
    SHELL_NAME


class RealDebugInstance(TestCase):
    def setUp(self) -> None:
        self._load_env_vars()
        self._real_api = CloudShellAPISession(self._cs_server, self._cs_user, self._cs_pass, self._cs_domain)

        self._context = None
        self._prepare_context()
        self._driver = self._create_driver()

        api = self._real_api
        res_id = self._context.reservation.reservation_id
        service_resource = TerraformService2G.create_from_context(self._context)
        self._logger = get_qs_logger(log_group=self._context.resource.name)
        self._driver_helper_object = DriverHelperObject(api, res_id, service_resource, self._logger)

    def _load_env_vars(self):
        load_dotenv()
        self._cs_user = os.environ.get("CS_USERNAME")
        self._cs_pass = os.environ.get("CS_PASSWORD")
        self._cs_server = os.environ.get("CS_SERVER")
        self._cs_domain = os.environ.get("RESERVATION_DOMAIN")
        self._cs_res_id = os.environ.get("RESERVATION_ID")
        self._sb_service_alias = os.environ.get("SB_SERVICE_ALIAS")

    def _prepare_context(self):
        self._context = mock.create_autospec(ResourceCommandContext)

        self._context.connectivity = mock.MagicMock()
        self._context.connectivity.server_address = self._cs_server
        self._context.connectivity.admin_auth_token = self._real_api.authentication.xmlrpc_token

        self._context.resource = mock.MagicMock()
        self._context.resource.attributes = dict()
        self._context.resource.name = self._sb_service_alias
        self._set_context_resource_attributes()

        self._context.reservation = mock.MagicMock()
        self._context.reservation.reservation_id = self._cs_res_id
        self._context.reservation.domain = self._cs_domain

    def _set_context_resource_attributes(self):
        services = self._real_api.GetReservationDetails(self._cs_res_id).ReservationDescription.Services
        for service in services:
            if service.Alias == self._sb_service_alias:
                for attribute in service.Attributes:
                    self._context.resource.attributes[attribute.Name] = attribute.Value

    def _create_driver(self) -> TerraformService2GDriver:
        driver = TerraformService2GDriver()
        driver.initialize(self._context)
        return driver

    def test_execute_and_destory(self):

        self._context.resource.attributes[f"{SHELL_NAME}.Terraform Inputs"] = VAULT_TF_INPUTS
        self._context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = os.environ.get("GITHUB_TF_PRIVATE_VAULT_URL")
        self._context.resource.attributes[
            f"{SHELL_NAME}.UUID"] = ""
        self._real_api.ClearSandboxData(self._driver_helper_object.res_id)

        self._driver.execute_terraform(self._context)

        # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
        # And also replace the custom inputs and TF URL
        self._set_context_resource_attributes()
        self._context.resource.attributes[f"{SHELL_NAME}.Terraform Inputs"] = VAULT_TF_INPUTS
        self._context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = os.environ.get("GITHUB_TF_PRIVATE_VAULT_URL")

        self._driver.destroy_terraform(self._context)

    def _test_download_terraform_module(self, url: str):
        self._context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url
        service_resource = TerraformService2G.create_from_context(self._context)
        self._driver_helper_object = DriverHelperObject(self._real_api,
                                                        self._context.reservation.reservation_id,
                                                        service_resource,
                                                        self._logger)

        downloader = Downloader(self._driver_helper_object)
        tf_workingdir = downloader.download_terraform_module()
        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TF_HELLO_FILE)))

    def test_public_and_private_hello_dl(self):
        self._test_download_terraform_module(os.environ.get("GITHUB_TF_PRIVATE_HELLO_URL"))
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL)

    def test_download_terraform_executable(self):
        downloader = Downloader(self._driver_helper_object)
        tf_workingdir = downloader.download_terraform_module()
        downloader.download_terraform_executable(tf_workingdir)

        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE)))
        self.assertTrue(os.access(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE), os.X_OK))
