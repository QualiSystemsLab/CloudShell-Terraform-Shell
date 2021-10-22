from unittest.mock import patch, Mock

# from cloudshell.api.cloudshell_api import NameValuePair
from cloudshell.api.cloudshell_api import NameValuePair
from dotenv import load_dotenv
from tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES, INT_TEST_TF_VER, INT_TEST_CLP_RESOURSE
from typing import Callable

from tests.integration_tests.helper_objects.integration_context import IntegrationData

import os
from unittest import TestCase

from pathlib import Path

from tests.integration_tests.helper_services.service_attributes_factory import ServiceAttributesMockBuilder


class TestMockTerraformExecuteDestroy(TestCase):
    @classmethod
    def setUpClass(self):
        load_dotenv(Path('int_tests.env'))
        if os.path.isfile(Path('int_tests_secrets.env')):
            load_dotenv(Path('int_tests_secrets.env'))

    @patch('cloudshell.iac.terraform.services.object_factory.CloudShellSessionContext')
    def setUp(self, patched_api) -> None:

        self._prepare_mock_api()
        patched_api.return_value.get_api.return_value = self.mock_api

        self._mocked_tf_working_dir = ''
        self._prepare_mock_services()

        self.mock_api.GetReservationDetails.return_value.ReservationDescription.Services = [self._service1,
                                                                                            self._service2]
        self._prepare_integration_data()

    def _prepare_integration_data(self):
        self.integration_data1 = IntegrationData(self._service1.Alias, False, self.mock_api)
        self.integration_data2 = IntegrationData(self._service2.Alias, False, self.mock_api)

    def _prepare_mock_services(self):
        self._service1 = Mock()
        self._service1.Alias = os.environ.get("SB_SERVICE_ALIAS1")
        self._service1.Attributes = ServiceAttributesMockBuilder.create_empty_attributes()
        self._service2 = Mock()
        self._service2.Alias = os.environ.get("SB_SERVICE_ALIAS2")
        self._service2.Attributes = ServiceAttributesMockBuilder.create_empty_attributes()

    def _prepare_mock_api(self):
        self.mock_api = Mock()
        self.mock_api.DecryptPassword = _decrypt_password
        self.mock_api.GetResourceDetails.return_value.ResourceFamilyName = 'Cloud Provider'
        self.mock_api.GetResourceDetails.return_value.ResourceModelName = 'Microsoft Azure'
        self.mock_api.GetResourceDetails.return_value.ResourceAttributes = [
            NameValuePair(Name="Azure Subscription ID", Value=os.environ.get("AZURE_SUBSCRIPTION_ID")),
            NameValuePair(Name="Azure Tenant ID", Value=os.environ.get("AZURE_TENANT_ID")),
            NameValuePair(Name="Azure Application ID", Value=os.environ.get("AZURE_APPLICATION_ID")),
            NameValuePair(Name="Azure Application Key", Value=os.environ.get("AZURE_APPLICATION_KEY_DEC"))
        ]

    '''------------------------------ Generic Execute/Destroy functions ---------------------------------'''

    def run_execute(self, pre_exec_function: Callable, integration_data: IntegrationData):
        self.pre_exec_prep(pre_exec_function, integration_data)
        integration_data.tf_shell.execute_terraform()

    def run_destroy(self, pre_destroy_function: Callable, integration_data: IntegrationData):
        self.pre_destroy_prep(pre_destroy_function, integration_data)
        integration_data.tf_shell.destroy_terraform()

    def run_execute_and_destroy(self, pre_exec_function: Callable, pre_destroy_function: Callable,
                                integration_data: IntegrationData):
        self.run_execute(pre_exec_function, integration_data)
        self.run_destroy(pre_destroy_function, integration_data)

    '''------------------------------ Test Cases ---------------------------------'''

    @patch('cloudshell.iac.terraform.services.tf_proc_exec.TfProcExec.can_destroy_run')
    @patch('cloudshell.iac.terraform.terraform_shell.SandboxDataHandler')
    @patch('cloudshell.iac.terraform.services.object_factory.CloudShellSessionContext')
    def test_execute_and_destroy_azure_vault(self, patch_api, patched_sbdata_handler, can_destroy_run):
        can_destroy_run.return_value = True
        patch_api.return_value.get_api.return_value = self.mock_api
        mock_sbdata_handler = Mock()
        mock_sbdata_handler.get_tf_working_dir = self._get_mocked_tf_working_dir
        mock_sbdata_handler.set_tf_working_dir = self._set_mocked_tf_working_dir
        patched_sbdata_handler.return_value = mock_sbdata_handler
        self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )

    '''------------------------------ Functions : general _pre prep functions ---------------------------------'''

    def pre_exec_prep(self, pre_exec_function: Callable, integration_data: IntegrationData):
        pre_exec_function(integration_data)

    def pre_destroy_prep(self, pre_destroy_function: Callable, integration_data: IntegrationData):
        pre_destroy_function(integration_data)

    def clear_sb_data(self):
        self.integration_data1.api.ClearSandboxData(self.integration_data1.context.reservation.reservation_id)

    '''------------------------------ Functions : prep before exec -------------------------------------------'''

    def pre_exec(self, integration_data: IntegrationData):
        pass

    def pre_exec_azure_vault(self, integration_data: IntegrationData):
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Terraform Inputs",
            os.environ.get("AZUREAPP_TF_INPUTS"),
            integration_data
        )
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Github Terraform Module URL",
            os.environ.get("GH_TF_PRIVATE_AZUREAPP_URL"),
            integration_data
        )
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TOKEN}",
            os.environ.get("GH_TOKEN_DEC"),
            integration_data
        )
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}",
            INT_TEST_TF_VER,
            integration_data
        )
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CLOUD_PROVIDER}",
            INT_TEST_CLP_RESOURSE,
            integration_data
        )
        self._prepare_service1_before_execute(integration_data)

    def _prepare_service1_before_execute(self, integration_data):
        service1 = Mock()
        service1.Alias = integration_data.context.resource.name
        service1.Attributes = integration_data.context.resource.attributes
        self.mock_api.GetReservationDetails.return_value.ReservationDescription.Services = [service1]
        integration_data.create_tf_shell()

    def pre_exec_azure_mssql(self, integration_data: IntegrationData):
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Terraform Inputs",
            os.environ.get("AZUREMSSQL_TF_INPUTS"),
            integration_data
        )
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Github Terraform Module URL",
            os.environ.get("GH_TF_PRIVATE_AZUREMSSQL_URL"),
            integration_data
        )
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.UUID",
            os.environ.get(""),
            integration_data
        )
        self._prepare_service1_before_execute(integration_data)

    def pre_exec_azure_vault_with_remote_access_key_based(self, integration_data: IntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_ACCESS_KEY"),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_cloud_cred_based(self, integration_data: IntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_CLOUD_CRED"),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_invalid_nonexistent(self, integration_data: IntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_INVALID_NO_RESOURCE"),
            integration_data
        )

    def pre_exec_azure_vault_with_remote_invalid_wrong(self, integration_data: IntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get("REMOTE_STATE_PROVIDER_INVALID_WRONG_RESOURCE"),
            integration_data
        )

    def pre_exec_azure_vault_without_remote(self, integration_data: IntegrationData):
        self.pre_exec_azure_vault(integration_data)
        self._set_attribute_on_mock_service(
            f"{SHELL_NAME}.Remote State Provider",
            os.environ.get(""),
            integration_data
        )

    '''------------------------------ Functions : prep before destroy -----------------------------------------'''

    def pre_destroy(self, integration_data: IntegrationData):
        # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
        for attribute in integration_data.context.resource.attributes:
            if attribute.Name == f"{SHELL_NAME}.UUID":
                attribute.Value = integration_data.tf_shell._tf_service.attributes[f"{SHELL_NAME}.UUID"]

    '''------------------------------ Helper Functions ---------------------------------------------------------'''
    @staticmethod
    def _set_attribute_on_mock_service(attr_name: str, attr_value: str, integration_data: IntegrationData):
        for attribute in integration_data.context.resource.attributes:
            if attribute.Name == attr_name:
                attribute.Value = attr_value
                return

    def _get_mocked_tf_working_dir(self):
        return self._mocked_tf_working_dir

    def _set_mocked_tf_working_dir(self, tf_working_dir: str):
        self._mocked_tf_working_dir = tf_working_dir


def _decrypt_password(x):
    # result = mock.MagicMock()
    result = Mock()
    result.Value = x
    return result
