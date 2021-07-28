import function as function
from cloudshell.api.cloudshell_api import AttributeNameValue

from tests.integration_tests.helper_objects.integration_context import IntegrationData

import os
from unittest import TestCase

SHELL_NAME = "Generic Terraform Service"


class TestTerraformExecuteDestroy(TestCase):
    def setUp(self) -> None:
        self.integration_data = IntegrationData()

    def run_execute_and_destroy(self, pre_exec_function: function, pre_destroy_function: function):

        self.pre_exec_prep(pre_exec_function)
        self.integration_data.driver.execute_terraform(self.integration_data.context)

        self.pre_destroy_prep(pre_destroy_function)
        self.integration_data.driver.destroy_terraform(self.integration_data.context)

    '''------------------------------ Test Cases ---------------------------------'''

    def test_execute_and_destroy(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec,
            pre_destroy_function=self.pre_destroy
        )

    def test_execute_and_destroy_azure_vault(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault,
            pre_destroy_function=self.pre_destroy
        )

    def test_execute_and_destroy_azure_vault_with_remote_access_key_based(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_with_remote_access_key_based,
            pre_destroy_function=self.pre_destroy
        )

    def test_execute_and_destroy_azure_vault_with_remote_access_cloud_cred_based(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_with_remote_cloud_cred_based,
            pre_destroy_function=self.pre_destroy
        )

    def test_execute_and_destroy_azure_vault_with_remote_invalid_nonexistent(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_with_remote_invalid_nonexistent,
            pre_destroy_function=self.pre_destroy
        )

    def test_execute_and_destroy_azure_vault_with_remote_invalid_wrong(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_with_remote_invalid_wrong,
            pre_destroy_function=self.pre_destroy
        )

    def test_execute_and_destroy_azure_vault_without_remote(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_without_remote,
            pre_destroy_function=self.pre_destroy
        )

    '''------------------------------ Functions : general _pre prep functions ---------------------------------'''

    def pre_exec_prep(self, pre_exec_function: function):
        pre_exec_function()
        self.integration_data.real_api.ClearSandboxData(self.integration_data.context.reservation.reservation_id)

    def pre_destroy_prep(self, pre_destroy_function: function):
        pre_destroy_function()

    '''------------------------------ Functions : prep before exec -------------------------------------------'''

    def pre_exec(self):
        pass

    def pre_exec_azure_vault(self):
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Terraform Inputs",
            os.environ.get("AZUREAPP_TF_INPUTS")
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Github Terraform Module URL",
            os.environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL")
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.UUID",
            os.environ.get("")
        )
        '''
        self.integration_data.context.resource.attributes[f"{SHELL_NAME}.Terraform Inputs"] = \
            os.environ.get("AZUREAPP_TF_INPUTS")
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Github Terraform Module URL"] = os.environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL")
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.UUID"] = ""
        '''

    def pre_exec_azure_vault_with_remote_access_key_based(self):
        self.pre_exec_azure_vault()
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_ACCESS_KEY")
        )
        '''
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Remote State Provider"] = os.environ.get("REMOTE_STATE_PROVIDER_ACCESS_KEY")
        '''

    def pre_exec_azure_vault_with_remote_cloud_cred_based(self):
        self.pre_exec_azure_vault()
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_CLOUD_CRED")
        )
        '''
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Remote State Provider"] = os.environ.get("REMOTE_STATE_PROVIDER_CLOUD_CRED")
        '''

    def pre_exec_azure_vault_with_remote_invalid_nonexistent(self):
        self.pre_exec_azure_vault()
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_INVALID_NO_RESOURCE")
        )
        '''
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Remote State Provider"] = os.environ.get("REMOTE_STATE_PROVIDER_INVALID_NO_RESOURCE")
        '''

    def pre_exec_azure_vault_with_remote_invalid_wrong(self):
        self.pre_exec_azure_vault()
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_INVALID_WRONG_RESOURCE")
        )
        '''
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Remote State Provider"] = os.environ.get("REMOTE_STATE_PROVIDER_INVALID_WRONG_RESOURCE")
        '''

    def pre_exec_azure_vault_without_remote(self):
        self.pre_exec_azure_vault()
        self._set_attribute_on_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("")
        )
        '''
        self.integration_data.context.resource.attributes[
            f"{SHELL_NAME}.Remote State Provider"] = os.environ.get("")
        '''

    '''------------------------------ Functions : prep before destroy -----------------------------------------'''

    def pre_destroy(self):
        # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
        self.integration_data.set_context_resource_attributes(f"{SHELL_NAME}.UUID")

    '''------------------------------ Helper Functions ---------------------------------------------------------'''

    def _set_attribute_on_service(self,attr_name: str, attr_value: str):
        attr_req = [AttributeNameValue(attr_name, attr_value)]
        self.integration_data.real_api.SetServiceAttributesValues(
            self.integration_data.context.reservation.reservation_id,
            self.integration_data.context.resource.name,
            attr_req
        )
