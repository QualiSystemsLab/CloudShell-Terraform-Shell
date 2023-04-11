from __future__ import annotations

import re
from enum import Enum
from functools import lru_cache

from cloudshell.cp.terraform.exceptions import InvalidResourceAttributeValue
from cloudshell.shell.standards.core.resource_config_entities import (
    ResourceAttrRO,
    ResourceBoolAttrRO,
)

COLLECTION_SEPARATOR_PATTERN = re.compile(r"[,;]")
KEY_VALUE_SEPARATOR_PATTERN = re.compile(r"[=]")


class TerraformDeploymentAppAttributeNames:
    git_terraform_url = "Git Terraform Module Path"
    branch = "Branch"
    terraform_app_inputs_map = "Terraform App Inputs Map"
    terraform_app_outputs_map = "Terraform App Outputs Map"
    terraform_inputs = "Terraform Inputs"
    terraform_sensitive_inputs = "Terraform Sensitive Inputs"
    cloud_provider = "Cloud Provider"
    custom_tags = "Custom Tags"
    autogenerated_name = "Autogenerated Name"


class TerraformResourceAttributeNames:
    git_provider = "Git Provider"
    git_token = "Git Token"
    git_terraform_url = "Git Terraform Module Path"
    branch = "Branch"
    local_terraform = "Local Terraform"
    terraform_version = "Terraform Version"
    cloud_provider = "Cloud Provider"
    remote_state_provider = "Remote State Provider"
    custom_tags = "Custom Tags"
    apply_tags = "Apply Tags"


class GitProvider(Enum):
    GitHub = "github"
    GitLab = "gitlab"


class PasswordAttrRO(ResourceAttrRO):
    @lru_cache
    def _decrypt_password(self, api, attr_value):
        """Decrypt password.

        :param cloudshell.api.cloudshell_api.CloudShellAPISession api:
        :param str attr_value:
        :return:
        """
        if api:
            return api.DecryptPassword(attr_value).Value
        raise InvalidResourceAttributeValue(
            "Cannot decrypt password, API is not defined"
        )

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: str
        """
        val = super().__get__(instance, owner)
        if val is self or val is self.default:
            return val
        return self._decrypt_password(instance._cs_api, val)


class ResourceAttrROShellName(ResourceAttrRO):
    def __init__(self, name, namespace=ResourceAttrRO.NAMESPACE.SHELL_NAME):
        super().__init__(name, namespace)


class ResourceBoolAttrROShellName(ResourceBoolAttrRO):
    def __init__(self, name, namespace=ResourceAttrRO.NAMESPACE.SHELL_NAME):
        super().__init__(name, namespace)


class CustomTagsAttrRO(ResourceAttrRO):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        attr = instance.attributes.get(self.get_key(instance), self.default)
        if attr:
            try:
                return {
                    key.strip(): val.strip()
                    for key, val in [
                        KEY_VALUE_SEPARATOR_PATTERN.split(data)
                        for data in filter(
                            bool,
                            map(str.strip, COLLECTION_SEPARATOR_PATTERN.split(attr)),
                        )
                    ]
                }
            except ValueError:
                raise InvalidResourceAttributeValue(
                    "'Custom Tags' attribute format is incorrect"
                )

        return {}


class ResourceBoolAttrRODeploymentPath(ResourceBoolAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)


class ResourceAttrRODeploymentPath(ResourceAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)


class ResourceDictAttrRODeploymentPath(CustomTagsAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)


class ResourceDictPasswordAttrRODeploymentPath(PasswordAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)

    def __get__(self, instance, owner):
        attr = super().__get__(instance, owner)
        if attr:
            try:
                return {
                    key.strip(): val.strip()
                    for key, val in [
                        KEY_VALUE_SEPARATOR_PATTERN.split(data)
                        for data in filter(
                            bool,
                            map(str.strip, COLLECTION_SEPARATOR_PATTERN.split(attr)),
                        )
                    ]
                }
            except ValueError:
                raise InvalidResourceAttributeValue(
                    "'Terraform Sensitive Inputs' attribute format is incorrect"
                )

        return {}


class ResourcePasswordAttrRODeploymentPath(PasswordAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)


class GitProviderAttrRO(ResourceAttrRO):
    def __init__(self):
        super().__init__(
            TerraformResourceAttributeNames.git_provider,
            ResourceAttrROShellName.NAMESPACE.SHELL_NAME,
        )

    def __get__(self, instance, owner) -> GitProvider:
        val = super().__get__(instance, owner)
        if val is self:
            return val
        try:
            return GitProvider(val)
        except ValueError:
            return GitProvider.GitHub
