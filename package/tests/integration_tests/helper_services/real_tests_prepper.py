import os

from cloudshell.api.cloudshell_api import AttributeNameValue

from package.tests.integration_tests.helper_objects.integration_context import RealAPIIntegrationData
from package.tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES, INT_TEST_TF_VER


def pre_exec_azure_vault(integration_data: RealAPIIntegrationData):
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}",
        os.environ.get("AZUREAPP_TF_INPUTS"),
        integration_data
    )
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}",
        os.environ.get("GITHUB_TF_PRIVATE_AZUREAPP_URL"),
        integration_data
    )
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}",
        INT_TEST_TF_VER,
        integration_data
    )
    set_attribute_on_service(
        f"{SHELL_NAME}.UUID",
        os.environ.get(""),
        integration_data
    )


def pre_exec_azure_vault_with_remote_access_key_based(integration_data: RealAPIIntegrationData):
    pre_exec_azure_vault(integration_data)
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
        os.environ.get("REMOTE_STATE_PROVIDER_ACCESS_KEY"),
        integration_data
    )


def pre_exec_azure_vault_with_remote_cloud_cred_based(integration_data: RealAPIIntegrationData):
    pre_exec_azure_vault(integration_data)
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
        os.environ.get("REMOTE_STATE_PROVIDER_CLOUD_CRED"),
        integration_data
    )


def pre_exec_azure_vault_with_remote_invalid_wrong(integration_data: RealAPIIntegrationData):
    pre_exec_azure_vault(integration_data)
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
        os.environ.get("REMOTE_STATE_PROVIDER_INVALID_WRONG_RESOURCE"),
        integration_data
    )


def pre_exec_azure_vault_with_remote_invalid_nonexistent(integration_data: RealAPIIntegrationData):
    pre_exec_azure_vault(integration_data)
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
        os.environ.get("REMOTE_STATE_PROVIDER_INVALID_NO_RESOURCE"),
        integration_data
    )


def pre_exec_azure_mssql(integration_data: RealAPIIntegrationData):
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}",
        os.environ.get("AZUREMSSQL_TF_INPUTS"),
        integration_data
    )
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}",
        os.environ.get("GITHUB_TF_PRIVATE_AZUREMSSQL_URL"),
        integration_data
    )
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}",
        os.environ.get(""),
        integration_data
    )


def post_vault_cleanup(integration_data: RealAPIIntegrationData):
    set_attribute_on_service(
        f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}",
        "",
        integration_data
    )


def set_attribute_on_service(attr_name: str, attr_value: str, integration_data: RealAPIIntegrationData):
    attr_req = [AttributeNameValue(attr_name, attr_value)]
    integration_data.api.SetServiceAttributesValues(
        integration_data.context.reservation.reservation_id,
        integration_data.context.resource.name,
        attr_req
    )
