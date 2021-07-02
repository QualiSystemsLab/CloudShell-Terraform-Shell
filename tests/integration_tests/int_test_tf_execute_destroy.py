import time
from os import environ
from unittest import TestCase

from tests.constants import TF_HELLO_DEFAULT_OUTPUT
from tests.integration_tests.helpers.integration_tests_data import IntegrationTestsData


class TestTerraformExecuteDestroy(TestCase):

    def setUp(self) -> None:
        self.data = IntegrationTestsData()
        self.data.real_api.ClearSandboxData(self.data.driver_helper.res_id)
        self.data.set_attribute("UUID")
        self.data.set_attribute("Terraform Output")

    def test_execute_and_destroy(self):
        # Testing the following:
        # 1) The download of a private Repo that has an app that needs Azure Access (so tests providers as well)
        # 2) The download of TF Executable
        # 3) The execution and destruction of the module

        self.data.set_attribute("Terraform Inputs",
                                environ.get("AZUREAPP_TF_INPUTS"))
        self.data.set_attribute("Github Terraform Module URL",
                                environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL"))

        self.data.driver.execute_terraform(self.data.context)

        # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
        # And also replace the custom inputs and TF URL
        self.data.set_context_resource_attributes()
        self.data.set_attribute("Terraform Inputs",
                                environ.get("AZUREAPP_TF_INPUTS"))
        self.data.set_attribute("Github Terraform Module URL",
                                environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL"))

        self.data.driver.destroy_terraform(self.data.context)

    def _test_execute_terraform_input_output(self, inputs: str, outputs: str):
        # Arrange
        self.data.set_attribute("Github Terraform Module URL", environ.get("GITHUB_TF_PRIVATE_HELLO_URL"))
        self.data.set_attribute("Terraform Inputs", inputs)

        # Act
        self.data.driver.execute_terraform(self.data.context)

        # Assert
        self.assertEqual(self.data.get_attribute("Terraform Output"), outputs)

    def test_execute_terraform_without_input(self):
        self._test_execute_terraform_input_output("", TF_HELLO_DEFAULT_OUTPUT)

    def test_execute_terraform_with_input(self):
        self._test_execute_terraform_input_output("hello=Test!", "hello=Test!")
