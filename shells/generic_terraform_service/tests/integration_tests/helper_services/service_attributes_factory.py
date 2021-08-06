from tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES


class ServiceAttributesFactory:
    def __init__(self):
        self.attributes = {}
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.BRANCH}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CUSTOM_TAGS}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.APPLY_TAGS}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TERRAFORM_MODULE_URL}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TERRAFORM_VERSION}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.GITHUB_TOKEN}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.CLOUD_PROVIDER}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_OUTPUTS}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_SENSIITVE_OUTPUTS}"] = ""
        self.attributes[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_INPUTS}"] = ""
