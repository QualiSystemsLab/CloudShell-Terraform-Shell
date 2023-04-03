from __future__ import annotations

from enum import Enum
from typing import Union

# from attr import field
from attrs import define, field
from cloudshell.shell.core.driver_context import (
    AutoLoadCommandContext,
    ResourceCommandContext,
    ResourceRemoteCommandContext, UnreservedResourceCommandContext,
)
from cloudshell.shell.standards.core.resource_conf import BaseConfig, attr
from cloudshell.shell.standards.core.resource_conf.enum import EnumCaseInsensitive


from cloudshell.cp.terraform.models.cs_resource_details_attrs_converter import \
    RemoteResourceAttrsConverter




CONTEXT_TYPES = Union[
    ResourceCommandContext,
    AutoLoadCommandContext,
    ResourceRemoteCommandContext,
    UnreservedResourceCommandContext,
]


class ShutdownMethod(Enum):
    SOFT = "soft"
    HARD = "hard"


class TFAttributeNames:
    git_provider = "Git Provider"
    git_token = "Git Token"
    git_terraform_url = "Git Terraform URL"
    branch = "Branch"
    local_terraform = "Local Terraform"
    terraform_version = "Terraform Version"
    cloud_provider = "Cloud Provider"
    remote_state_provider = "Remote State Provider"
    custom_tags = "Custom Tags"
    apply_tags = "Apply Tags"


class GitProvider(EnumCaseInsensitive):
    GitHub = "github"
    GitLab = "gitlab"


@define(slots=False, str=False)
class TerraformResourceConfig(BaseConfig):
    _REMOTE_CONTEXT_CONVERTER = RemoteResourceAttrsConverter
    ATTR_NAMES = TFAttributeNames

    git_provider: GitProvider = attr(
        ATTR_NAMES.git_provider,
        default=GitProvider.GitHub
    )
    git_token: str = attr(ATTR_NAMES.git_token, is_password=True)
    git_terraform_url: str = attr(ATTR_NAMES.git_terraform_url)
    branch: str = attr(ATTR_NAMES.branch)
    local_terraform: str = attr(ATTR_NAMES.local_terraform)
    terraform_version: str = attr(ATTR_NAMES.terraform_version)
    cloud_provider: str = attr(ATTR_NAMES.cloud_provider)
    remote_state_provider: str = attr(ATTR_NAMES.remote_state_provider)
    custom_tags: str = attr(ATTR_NAMES.custom_tags)
    apply_tags: bool = attr(ATTR_NAMES.apply_tags)
    cp_custom_tags: dict = field(init=False)

    def __attrs_post_init__(self):
        self.cp_custom_tags = self._parse_custom_tags(self.custom_tags)

    def _parse_custom_tags(self, tags: str) -> dict[str: str]:
        if not tags:
            return {}
        return {tag.split("=")[0]: tag.split("=")[1] for tag in tags.split(";")}

    # write_sandbox_messages = False
    # update_live_status = False
    # inputs_map = {}
    # outputs_map = {}

    # @classmethod
    # def from_cs_resource_details(
    #         cls,
    #         details: ResourceInfo,
    #         shell_name: str = SHELL_NAME,
    #         api=None,
    #         supported_os=None,
    # ) -> TerraformResourceConfig:
    #     attrs = {attr.Name: attr.Value for attr in details.ResourceAttributes}
    #     converter = cls._CONVERTER(context, cls, _password_decryptor(api))
    #     return cls(
    #         shell_name=shell_name,
    #         name=details.Name,
    #         fullname=details.Name,
    #         address=details.Address,
    #         family_name=details.ResourceFamilyName,
    #         attributes=attrs,
    #         supported_os=supported_os,
    #         api=api,
    #         cs_resource_id=details.UniqeIdentifier,
    #     )
