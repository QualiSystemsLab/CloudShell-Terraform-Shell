from __future__ import annotations

from typing import Union

from cloudshell.api.cloudshell_api import CloudShellAPISession, ResourceInfo
from cloudshell.cp.terraform.constants import SHELL_NAME
from cloudshell.cp.terraform.models.base_deployment_app import (
    GitProviderAttrRO,
    ResourceAttrROShellName,
    ResourceBoolAttrROShellName,
    TerraformResourceAttributeNames,
)
from cloudshell.shell.core.driver_context import (
    AutoLoadCommandContext,
    ResourceCommandContext,
    ResourceRemoteCommandContext,
)
from cloudshell.shell.standards.core.resource_config_entities import (
    GenericResourceConfig,
    PasswordAttrRO,
    ResourceListAttrRO,
)

CONTEXT_TYPES = Union[
    ResourceCommandContext,
    AutoLoadCommandContext,
    ResourceRemoteCommandContext,
]


class TerraformResourceConfig(GenericResourceConfig):
    ATTR_NAMES = TerraformResourceAttributeNames

    git_provider = GitProviderAttrRO()
    git_token = PasswordAttrRO(
        ATTR_NAMES.git_token, PasswordAttrRO.NAMESPACE.SHELL_NAME
    )
    git_terraform_url = ResourceAttrROShellName(ATTR_NAMES.git_terraform_url)
    branch = ResourceAttrROShellName(ATTR_NAMES.branch)
    local_terraform = ResourceAttrROShellName(ATTR_NAMES.local_terraform)
    terraform_version = ResourceAttrROShellName(ATTR_NAMES.terraform_version)
    cloud_provider = ResourceAttrROShellName(ATTR_NAMES.cloud_provider)
    remote_state_provider = ResourceAttrROShellName(ATTR_NAMES.remote_state_provider)
    custom_tags = ResourceListAttrRO(
        ATTR_NAMES.custom_tags, ResourceListAttrRO.NAMESPACE.SHELL_NAME
    )
    apply_tags = ResourceBoolAttrROShellName(ATTR_NAMES.apply_tags)

    @classmethod
    def from_context(
        cls,
        context: CONTEXT_TYPES,
        shell_name: str = SHELL_NAME,
        api: CloudShellAPISession | None = None,
        supported_os: list[str] | None = None,
    ) -> TerraformResourceConfig:
        # noinspection PyTypeChecker
        # return type is VCenterResourceConfig not GenericResourceConfig
        return super().from_context(
            context=context, shell_name=shell_name, api=api, supported_os=supported_os
        )

    @classmethod
    def from_cs_resource_details(
        cls,
        details: ResourceInfo,
        shell_name: str = SHELL_NAME,
        api=None,
        supported_os=None,
    ) -> TerraformResourceConfig:
        attrs = {attr.Name: attr.Value for attr in details.ResourceAttributes}
        return cls(
            shell_name=shell_name,
            name=details.Name,
            fullname=details.Name,
            address=details.Address,
            family_name=details.ResourceFamilyName,
            attributes=attrs,
            supported_os=supported_os,
            api=api,
            cs_resource_id=details.UniqeIdentifier,
        )
