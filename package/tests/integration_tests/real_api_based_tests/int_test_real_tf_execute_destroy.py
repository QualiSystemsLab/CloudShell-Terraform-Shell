from cloudshell.api.cloudshell_api import AttributeNameValue
from dotenv import load_dotenv
from tests.integration_tests.constants import SHELL_NAME
from typing import Callable
from tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES, INT_TEST_TF_VER

from tests.integration_tests.helper_objects.integration_context import RealAPIIntegrationData

import os
from pathlib import Path
from unittest import TestCase


class TestRealTerraformExecuteDestroy(TestCase):
    @classmethod
    def setUpClass(self):
        load_dotenv(Path('../int_tests.env'))
        if os.path.isfile(Path('../int_tests_secrets.env')):
            load_dotenv(Path('../int_tests_secrets.env'))

    def setUp(self) -> None:
        self.integration_data1 = RealAPIIntegrationData(os.environ.get("SB_SERVICE_ALIAS1"))
        self.integration_data2 = RealAPIIntegrationData(os.environ.get("SB_SERVICE_ALIAS2"))

    def run_execute_and_destroy(
            self, pre_exec_function: Callable,
            pre_destroy_function: Callable,
            integration_data: RealAPIIntegrationData
    ):
        self.clear_sb_data()
        self.run_execute(pre_exec_function, integration_data)
        self.run_destroy(pre_destroy_function, integration_data)

    def run_execute(self, pre_exec_function: Callable, integration_data: RealAPIIntegrationData):
        self.pre_exec_prep(pre_exec_function, integration_data)
        integration_data.tf_shell.execute_terraform()

    def run_destroy(self, pre_destroy_function: Callable, integration_data: RealAPIIntegrationData):
        self.pre_destroy_prep(pre_destroy_function, integration_data)
        integration_data.tf_shell.destroy_terraform()

    '''------------------------------ Test Cases ---------------------------------'''

    def test_execute_and_destroy(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )

    def test_execute_and_destroy_azure_vault(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )

    def test_execute_dual_mssql(self):
        self.clear_sb_data()
        try:
            self.run_execute(pre_exec_function=self.pre_exec_azure_mssql, integration_data=self.integration_data1)
        except Exception as e:
            pass
        try:
            self.run_execute(pre_exec_function=self.pre_exec_azure_mssql, integration_data=self.integration_data2)
        except Exception as e:
            print("Error")
            pass
        self.run_destroy(pre_destroy_function=self.pre_destroy, integration_data=self.integration_data1)
        self.run_execute(pre_exec_function=self.pre_exec_azure_mssql, integration_data=self.integration_data2)

    def test_execute_and_destroy_azure_vault_with_remote_access_key_based(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_with_remote_access_key_based,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )

    def test_execute_and_destroy_azure_vault_with_remote_access_cloud_cred_based(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_with_remote_cloud_cred_based,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )

    def test_execute_and_destroy_azure_vault_with_remote_invalid_nonexistent(self):
        try:
            self.run_execute_and_destroy(
                pre_exec_function=self.pre_exec_azure_vault_with_remote_invalid_nonexistent,
                pre_destroy_function=self.pre_destroy,
                integration_data=self.integration_data1
            )
        except Exception as e:
            pass

    def test_execute_and_destroy_azure_vault_with_remote_invalid_wrong(self):
        try:
            self.run_execute_and_destroy(
                pre_exec_function=self.pre_exec_azure_vault_with_remote_invalid_wrong,
                pre_destroy_function=self.pre_destroy,
                integration_data=self.integration_data1
            )
        except Exception as e:
            pass

    def test_execute_and_destroy_azure_vault_without_remote(self):
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault_without_remote,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )

    '''------------------------------ Functions : general _pre prep functions ---------------------------------'''

    def pre_exec_prep(self, pre_exec_function: Callable, integration_data: RealAPIIntegrationData):
        pre_exec_function(integration_data)

    def pre_destroy_prep(self, pre_destroy_function: Callable, integration_data: RealAPIIntegrationData):
        pre_destroy_function(integration_data)

    def clear_sb_data(self):
        self.integration_data1.api.ClearSandboxData(self.integration_data1.context.reservation.reservation_id)

    '''------------------------------ Functions : prep before exec -------------------------------------------'''

    def pre_exec(self, integration_data: RealAPIIntegrationData):
        pass

    def pre_exec_azure_vault(self, integration_data: RealAPIIntegrationData):
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}",
            os.environ.get("AZUREAPP_TF_INPUTS"),
            integration_data
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}",
            os.environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL"),
            integration_data
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}",
            INT_TEST_TF_VER,
            integration_data
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.UUID",
            os.environ.get(""),
            integration_data
        )

    def pre_exec_azure_mssql(self, integration_data: RealAPIIntegrationData):
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}",
            os.environ.get("AZUREMSSQL_TF_INPUTS"),
            integration_data
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}",
            os.environ.get("GITHUB_TF_PRIVATE_AZUREMSSQL_URL"),
            integration_data
        )
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}",
            os.environ.get(""),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_access_key_based(self, integration_data: RealAPIIntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
            os.environ.get("REMOTE_STATE_PROVIDER_ACCESS_KEY"),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_cloud_cred_based(self, integration_data: RealAPIIntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
            os.environ.get("REMOTE_STATE_PROVIDER_CLOUD_CRED"),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_invalid_nonexistent(self, integration_data: RealAPIIntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
            os.environ.get("REMOTE_STATE_PROVIDER_INVALID_NO_RESOURCE"),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_invalid_wrong(self, integration_data: RealAPIIntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
            os.environ.get("REMOTE_STATE_PROVIDER_INVALID_WRONG_RESOURCE"),
            integration_data
        )

    def pre_exec_azure_vault_without_remote(self, integration_data: RealAPIIntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
            os.environ.get(""),
            integration_data
        )

    '''------------------------------ Functions : prep before destroy -----------------------------------------'''

    def pre_destroy(self, integration_data: RealAPIIntegrationData):
        # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
        integration_data.set_context_resource_attributes_from_cs(f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}")

    '''------------------------------ Helper Functions ---------------------------------------------------------'''

    def _set_attribute_on_service(self, attr_name: str, attr_value: str, integration_data: RealAPIIntegrationData):
        attr_req = [AttributeNameValue(attr_name, attr_value)]
        integration_data.api.SetServiceAttributesValues(
            integration_data.context.reservation.reservation_id,
            integration_data.context.resource.name,
            attr_req
        )
