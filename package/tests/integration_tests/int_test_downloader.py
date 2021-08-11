import os
from unittest import TestCase

from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater
from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService
from shells.generic_terraform_service.src.data_model import GenericTerraformService
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from tests.constants import GITHUB_TF_PUBLIC_HELLO_URL_FILE, GITHUB_TF_PUBLIC_HELLO_URL_FOLDER, TERRAFORM_EXEC_FILE, \
    SHELL_NAME, TF_HELLO_FILE
from tests.integration_tests.helper_objects.integration_context import IntegrationData
from cloudshell.iac.terraform.tagging.tags import TagsManager
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler


class TestTerraformDownloader(TestCase):
    def setUp(self) -> None:
        self.integration_data = IntegrationData()

        service_resource = GenericTerraformService.create_from_context(self.integration_data.context)

        sandbox_messages = SandboxMessagesService(
            self.integration_data.real_api,
            self.integration_data.context.reservation.reservation_id,
            self.integration_data.context.resource.name,
            False
        )

        live_status_updater = LiveStatusUpdater(
            self.integration_data.real_api,
            self.integration_data.context.reservation.reservation_id,
            False
        )

        default_tags = TagsManager(self.integration_data.context.reservation)

        attr_handler = ServiceAttrHandler(service_resource)

        self._driver_helper = ShellHelperObject(
            self.integration_data.real_api,
            self.integration_data.context.reservation.reservation_id,
            service_resource,
            self.integration_data._logger,
            sandbox_messages,
            live_status_updater,
            attr_handler,
            default_tags
        )

    def _test_download_terraform_module(self, url: str, branch: str):
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url
        self._driver_helper.tf_service.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = url
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Branch"] = branch
        self._driver_helper.tf_service.attributes[
            f"{SHELL_NAME}.Branch"] = branch

        downloader = Downloader(self._driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TF_HELLO_FILE)))

    def test_public_and_private_hello_dl(self):
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL_FILE, "")
        self._test_download_terraform_module(os.environ.get("GITHUB_TF_PRIVATE_HELLO_URL"), "")
        self._test_download_terraform_module(GITHUB_TF_PUBLIC_HELLO_URL_FOLDER, "")

    def test_download_terraform_executable(self):
        downloader = Downloader(self._driver_helper)
        tf_workingdir = downloader.download_terraform_module()
        downloader.download_terraform_executable(tf_workingdir)

        self.assertTrue(os.path.exists(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE)))
        self.assertTrue(os.access(os.path.join(tf_workingdir, TERRAFORM_EXEC_FILE), os.X_OK))
