from __future__ import annotations

from cloudshell.cp.core.request_actions import DeployVMRequestActions
from cloudshell.cp.core.request_actions.models import DeployApp
from cloudshell.cp.terraform import constants
from cloudshell.cp.terraform.models.base_deployment_app import (
    ResourceAttrRODeploymentPath,
    ResourceBoolAttrRODeploymentPath,
    ResourceDictAttrRODeploymentPath,
    ResourceDictPasswordAttrRODeploymentPath,
    ResourcePasswordAttrRODeploymentPath,
    TerraformDeploymentAppAttributeNames,
)


class VMFromTerraformGit(DeployApp):
    _DO_NOT_EDIT_APP_NAME = True
    ATTR_NAMES = TerraformDeploymentAppAttributeNames
    DEPLOYMENT_PATH = constants.VM_FROM_TF_GIT

    autogenerated_name: str = ResourceBoolAttrRODeploymentPath(
        ATTR_NAMES.autogenerated_name
    )
    branch: str = ResourceAttrRODeploymentPath(ATTR_NAMES.branch)
    cloud_provider: str = ResourceAttrRODeploymentPath(ATTR_NAMES.cloud_provider)
    custom_tags: dict[str:str] = ResourceDictAttrRODeploymentPath(
        ATTR_NAMES.custom_tags
    )
    git_terraform_url: str = ResourceAttrRODeploymentPath(ATTR_NAMES.git_terraform_url)
    terraform_inputs: dict[str:str] = ResourceDictAttrRODeploymentPath(
        ATTR_NAMES.terraform_inputs
    )
    terraform_app_inputs_map: dict[str:str] = ResourceDictAttrRODeploymentPath(
        ATTR_NAMES.terraform_app_inputs_map
    )
    terraform_app_outputs_map: dict[str:str] = ResourceDictAttrRODeploymentPath(
        ATTR_NAMES.terraform_app_outputs_map
    )
    terraform_sensitive_inputs: dict[
        str:str
    ] = ResourceDictPasswordAttrRODeploymentPath(ATTR_NAMES.terraform_sensitive_inputs)

    def __post_init__(self):
        """Post init."""
        super().__post_init__()
        self.app_attrs_map = {}
        self.full_name_attrs_map = {}
        for attr_name, attr in self.attributes.items():
            if attr_name.startswith(self.DEPLOYMENT_PATH):
                continue
            self.app_attrs_map[attr_name.split(".")[-1]] = attr
            self.full_name_attrs_map[attr_name.split(".")[-1]] = attr_name

    def get_app_resource_attribute(self, attr_name):
        """Get App Resource attribute by its name.

        :param str attr_name:
        :return:
        """
        for attr, value in self.attributes.items():
            if any([attr == attr_name, attr.endswith(f".{attr_name}")]):
                return value

    def get_attributes_dict(self):
        """Get attribute dict by its name.

        :param str attr_name:
        :return:
        """
        return self.app_attrs_map

    def get_app_inputs(self) -> dict[str:str]:
        """Get the app inputs.

        :return: dict of app inputs
        :rtype: dict[str: str]
        """
        attributes = self.get_attributes_dict()
        inputs = {}

        for input_name, attribute_name in self.terraform_app_inputs_map.items():
            attr = attributes.get(attribute_name)
            if attr:
                inputs[input_name] = attr

        return inputs


class VMFromTerraformGitRequestActions(DeployVMRequestActions):
    deploy_app: VMFromTerraformGit
