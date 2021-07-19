import os
from unittest import TestCase
from unittest.mock import Mock

from dotenv import load_dotenv

from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from tests.constants import GITHUB_TF_PUBLIC_HELLO_URL_FILE, GITHUB_TF_PUBLIC_HELLO_URL_FOLDER, TERRAFORM_EXEC_FILE, \
    SHELL_NAME, TF_HELLO_FILE
from tests.integration_tests.helper_objects.integration_context import IntegrationData


class TestTerraformDownloader(TestCase):
    def setUp(self) -> None:
        self.integration_data = IntegrationData()
        load_dotenv()

    def _test_download_terraform_module(self, url: str):
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url

        service_resource = Mock()
        service_resource.github_token = os.environ.get("GITHUB_TOKEN_ENC")
        service_resource.github_terraform_module_url = url

        self.integration_data.driver_helper.tf_service.github_terraform_module_url = url
        downloader = Downloader(self.integration_data.driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TF_HELLO_FILE)))

    def test_public_and_private_hello_dl(self):
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL_FILE)
        self._test_download_terraform_module(os.environ.get("GITHUB_TF_PRIVATE_HELLO_URL"))
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL_FOLDER)

    def test_download_terraform_executable(self):
        self.integration_data.driver_helper.tf_service.github_terraform_module_url = GITHUB_TF_PUBLIC_HELLO_URL_FILE
        self.integration_data.driver_helper.tf_service.terraform_version = os.environ.get("TFEXEC_VERSION")
        downloader = Downloader(self.integration_data.driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        downloader.download_terraform_executable(tf_workingdir)

        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE)))
        self.assertTrue(os.access(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE), os.X_OK))