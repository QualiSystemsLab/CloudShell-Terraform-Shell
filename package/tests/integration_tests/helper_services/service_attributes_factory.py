from typing import List

from cloudshell.api.cloudshell_api import NameValuePair

from tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES


class ServiceAttributesMockBuilder:
    @staticmethod
    def create_empty_attributes() -> List[dict]:
        attributes = [
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.BRANCH}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CUSTOM_TAGS}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.APPLY_TAGS}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TOKEN}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CLOUD_PROVIDER}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_OUTPUTS}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_SENSIITVE_OUTPUTS}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}", Value="")
        ]
        return attributes
