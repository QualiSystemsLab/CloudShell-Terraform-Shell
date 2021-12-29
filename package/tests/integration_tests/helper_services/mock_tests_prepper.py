import os
from unittest.mock import Mock

from package.tests.integration_tests.helper_objects.integration_context import MockAPIIntegrationData
from package.tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES, INT_TEST_TF_VER, \
    INT_TEST_CLP_RESOURSE
from package.tests.integration_tests.helper_objects.mock_tests_data import MockTestsData



def pre_exec_azure_vault(mock_tests_data: MockTestsData, azure_vault_url: str):
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}",
        os.environ.get("AZUREAPP_TF_INPUTS"),
        mock_tests_data.integration_data1
    )
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}",
        azure_vault_url,
        mock_tests_data.integration_data1
    )
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TOKEN}",
        os.environ.get("GH_TOKEN_DEC"),
        mock_tests_data.integration_data1
    )
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}",
        INT_TEST_TF_VER,
        mock_tests_data.integration_data1
    )
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CLOUD_PROVIDER}",
        INT_TEST_CLP_RESOURSE,
        mock_tests_data.integration_data1
    )
    prepare_service1_before_execute(mock_tests_data, mock_tests_data.integration_data1)


def pre_exec_azure_mssql(mock_tests_data: MockTestsData,
                         integration_data: MockAPIIntegrationData):
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}",
        os.environ.get("AZUREMSSQL_TF_INPUTS"),
        integration_data
    )
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}",
        os.environ.get("GH_TF_PRIVATE_AZUREMSSQL_URL"),
        integration_data
    )
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.UUID",
        os.environ.get(""),
        integration_data
    )
    prepare_service1_before_execute(mock_tests_data, mock_tests_data.integration_data1)


def pre_exec_azure_vault_with_remote_access_key_based(mock_tests_data: MockTestsData,
                                                      integration_data: MockAPIIntegrationData):
    pre_exec_azure_vault(mock_tests_data)
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.Remote State Provider",
        os.environ.get("REMOTE_STATE_PROVIDER_ACCESS_KEY"),
        integration_data
    )


def pre_exec_azure_vault_with_remote_cloud_cred_based(mock_tests_data: MockTestsData,
                                                      integration_data: MockAPIIntegrationData):
    pre_exec_azure_vault(mock_tests_data)
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.Remote State Provider",
        os.environ.get("REMOTE_STATE_PROVIDER_CLOUD_CRED"),
        integration_data
    )


def pre_exec_azure_vault_with_remote_invalid_nonexistent(mock_tests_data: MockTestsData,
                                                         integration_data: MockAPIIntegrationData):
    pre_exec_azure_vault(mock_tests_data)
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.Remote State Provider",
        os.environ.get("REMOTE_STATE_PROVIDER_INVALID_NO_RESOURCE"),
        integration_data
    )


def pre_exec_azure_vault_with_remote_invalid_wrong(mock_tests_data: MockTestsData,
                                                   integration_data: MockAPIIntegrationData):
    pre_exec_azure_vault(mock_tests_data)
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.Remote State Provider",
        os.environ.get("REMOTE_STATE_PROVIDER_INVALID_WRONG_RESOURCE"),
        integration_data
    )


def pre_exec_azure_vault_without_remote(mock_tests_data: MockTestsData,
                                        integration_data: MockAPIIntegrationData):
    pre_exec_azure_vault(mock_tests_data)
    set_attribute_on_mock_service(
        f"{SHELL_NAME}.Remote State Provider",
        os.environ.get(""),
        integration_data
    )


def pre_destroy(integration_data: MockAPIIntegrationData):
    # As UUID has been created and SB data now contains UUID and Status we must update context so destroy can run
    for attribute in integration_data.context.resource.attributes:
        if attribute.Name == f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}":
            attribute.Value = integration_data.tf_shell._tf_service.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}"]


def prepare_service1_before_execute(mock_tests_data: MockTestsData, integration_data):
    service1 = Mock()
    service1.Alias = integration_data.context.resource.name
    service1.Attributes = integration_data.context.resource.attributes
    mock_tests_data.mock_api.GetReservationDetails.return_value.ReservationDescription.Services = [service1]
    integration_data.create_tf_shell()


def set_attribute_on_mock_service(attr_name: str, attr_value: str, integration_data: MockAPIIntegrationData):
    for attribute in integration_data.context.resource.attributes:
        if attribute.Name == attr_name:
            attribute.Value = attr_value
            return
