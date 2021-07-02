import os
from unittest import TestCase

from data_model import TerraformService2G
from downloaders.downloader import Downloader
from driver_helper_obj import DriverHelperObject
from tests.constants import TF_HELLO_FILE, TERRAFORM_EXEC_FILE, SHELL_NAME, GITHUB_TF_PUBLIC_HELLO_URL_FILE, \
    GITHUB_TF_PUBLIC_HELLO_URL_FOLDER
from tests.integration_tests.helper_objects.integration_context import IntegrationData


class TestTerraformExecuteDestroy(TestCase):
    def setUp(self) -> None:
        self.integration_data = IntegrationData()



    def test_execute_and_destroy(self):
        self.integration_data.context.resource.attributes[f"{SHELL_NAME}.Terraform Inputs"] = \
            os.environ.get(" VAULT_TF_INPUTS")
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = os.environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL")
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.UUID"] = ""

        self.integration_data.context.real_api.ClearSandboxData(self._driver_helper.res_id)

        self.integration_data.driver.execute_terraform(self.integration_data.context)

        # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
        # And also replace the custom inputs and TF URL
        self.integration_data.set_context_resource_attributes()
        self.integration_data.context.resource.attributes[f"{SHELL_NAME}.Terraform Inputs"] = \
            os.environ.get(" VAULT_TF_INPUTS")
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = os.environ.get("GITHUB_TF_PRIVATE_VAULT_URL")

        self.integration_data.driver.destroy_terraform(self.integration_data.context)

