import os
from unittest import TestCase
from pathlib import Path

from dotenv import load_dotenv

from unittest.mock import patch, Mock

from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from shells.generic_terraform_service.src.data_model import GenericTerraformService
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from package.tests.constants import GH_TF_PUBLIC_HELLO_URL_FILE, GH_TF_PUBLIC_HELLO_URL_FOLDER, TERRAFORM_EXEC_FILE, \
    SHELL_NAME, TF_HELLO_FILE, MOCK_ALIAS2, MOCK_ALIAS1
# from package.tests.integration_tests.helper_objects.downloader_integration_context import IntegrationData
from package.tests.integration_tests.helper_objects.integration_context import MockAPIIntegrationData

from cloudshell.iac.terraform.tagging.tags import TagsManager
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler
from package.tests.integration_tests.helper_services.service_attributes_factory import ServiceAttributesMockBuilder


class TestTerraformDownloader(TestCase):
    @classmethod
    def setUpClass(self):
        load_dotenv(Path('../int_tests.env'))
        if os.path.isfile(Path('../int_tests_secrets.env')):
            load_dotenv(Path('../int_tests_secrets.env'))

    @patch('cloudshell.iac.terraform.services.object_factory.CloudShellSessionContext')
    def setUp(self, patched_api) -> None:
        self._prepare_mock_api()

        self._mocked_tf_working_dir = ''
        self._prepare_mock_services()
        self.mock_api.GetReservationDetails.return_value.ReservationDescription.Services = [self._service1,
                                                                                            self._service2]
        self._prepare_integration_data()



        service_resource = GenericTerraformService.create_from_context(self.integration_data1.context)

        sandbox_messages = SandboxMessagesService(
            self.integration_data1.api,
            self.integration_data1.context.reservation.reservation_id,
            self.integration_data1.context.resource.name,
            False
        )

        live_status_updater = LiveStatusUpdater(
            self.integration_data1.api,
            self.integration_data1.context.reservation.reservation_id,
            False
        )

        default_tags = TagsManager(self.integration_data1.context.reservation)

        attr_handler = ServiceAttrHandler(service_resource)

        self._driver_helper = ShellHelperObject(
            self.integration_data1.api,
            self.integration_data1.context.reservation.reservation_id,
            service_resource,
            self.integration_data1._logger,
            sandbox_messages,
            live_status_updater,
            attr_handler,
            default_tags
        )

    def _prepare_integration_data(self):
        self.integration_data1 = MockAPIIntegrationData(self._service1.Alias, self.mock_api)
        self.integration_data2 = MockAPIIntegrationData(self._service2.Alias, self.mock_api)

    def _prepare_mock_api(self):
        self.mock_api = Mock()

    def _prepare_mock_services(self):
        self._service1 = Mock()
        self._service1.Alias = MOCK_ALIAS1
        self._service1.Attributes = ServiceAttributesMockBuilder.create_empty_attributes()
        self._service2 = Mock()
        self._service2.Alias = MOCK_ALIAS2
        self._service2.Attributes = ServiceAttributesMockBuilder.create_empty_attributes()

    def _test_download_terraform_module(self, url: str, branch: str):
        self.integration_data1.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url
        self._driver_helper.tf_service.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url
        self.integration_data1.context.resource.attributes[
            f"{SHELL_NAME}.Branch"] = branch
        self._driver_helper.tf_service.attributes[
            f"{SHELL_NAME}.Branch"] = branch

        downloader = Downloader(self._driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TF_HELLO_FILE)))

    def test_public_and_private_hello_dl(self):
        self._test_download_terraform_module(GH_TF_PUBLIC_HELLO_URL_FILE, "")
        self._test_download_terraform_module(os.environ.get("GITHUB_TF_PRIVATE_HELLO_URL"), "")
        self._test_download_terraform_module(GH_TF_PUBLIC_HELLO_URL_FOLDER, "")

    def test_download_terraform_executable(self):
        downloader = Downloader(self._driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        downloader.download_terraform_executable(tf_workingdir)

        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE)))
        self.assertTrue(os.access(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE), os.X_OK))
