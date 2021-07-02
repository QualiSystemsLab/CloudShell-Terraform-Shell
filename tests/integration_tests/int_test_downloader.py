import os
from unittest import TestCase

from data_model import TerraformService2G
from downloaders.downloader import Downloader
from driver_helper_obj import DriverHelperObject
from tests.constants import GITHUB_TF_PUBLIC_HELLO_URL_FILE, GITHUB_TF_PUBLIC_HELLO_URL_FOLDER, TERRAFORM_EXEC_FILE, \
    SHELL_NAME, TF_HELLO_FILE
from tests.integration_tests.helper_objects.integration_context import IntegrationData


class TestTerraformDownloader(TestCase):
    def setUp(self) -> None:
        self.integration_data = IntegrationData()

    def _test_download_terraform_module(self, url: str):
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url
        service_resource = TerraformService2G.create_from_context(self.integration_data.context)
        self._driver_helper = DriverHelperObject(self.integration_data.context.real_api,
                                                 self.integration_data.context.reservation.reservation_id,
                                                 service_resource,
                                                 self.integration_data._logger)

        downloader = Downloader(self._driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TF_HELLO_FILE)))

    def test_public_and_private_hello_dl(self):
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL_FILE)
        self._test_download_terraform_module(os.environ.get("GITHUB_TF_PRIVATE_HELLO_URL"))
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL_FOLDER)

    def test_download_terraform_executable(self):
        downloader = Downloader(self._driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        downloader.download_terraform_executable(tf_workingdir)

        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE)))
        self.assertTrue(os.access(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE), os.X_OK))