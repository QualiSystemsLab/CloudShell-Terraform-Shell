from cloudshell.api.cloudshell_api import NameValuePair

from tests.integration_tests.constants import ATTRIBUTE_NAMES, SHELL_NAME


class ServiceAttributesFactory:
    @staticmethod
    def create_empty_attributes() -> list[dict]:
        attributes = [
            NameValuePair(
                Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}", Value=""
            ),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.BRANCH}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CUSTOM_TAGS}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.APPLY_TAGS}", Value=""),
            NameValuePair(
                Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GIT_TERRAFORM_MODULE_URL}",
                Value="",
            ),
            NameValuePair(
                Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}", Value=""
            ),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GIT_TOKEN}", Value=""),
            NameValuePair(
                Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CLOUD_PROVIDER}", Value=""
            ),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}", Value=""),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_OUTPUTS}", Value=""),
            NameValuePair(
                Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_SENSIITVE_OUTPUTS}", Value=""
            ),
            NameValuePair(Name=f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}", Value=""),
        ]
        return attributes
