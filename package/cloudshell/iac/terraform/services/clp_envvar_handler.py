import os
from abc import ABCMeta

# from cloudshell.api.cloudshell_api import ResourceAttribute

from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class BaseCloudProviderEnvVarHandler(metaclass=ABCMeta):
    def __init__(self):
        pass

    def set_env_vars_based_on_clp(self):
        raise NotImplementedError()

    @staticmethod
    def get_attribute_value(clp_res_model, clp_attribute, attr_name_to_check, shell_helper, decrypt=False) -> str:
        if f"{clp_res_model}.{clp_attribute.Name}" == attr_name_to_check or clp_attribute.Name == attr_name_to_check:
            if decrypt:
                return shell_helper.api.DecryptPassword(clp_attribute.Value).Value
            else:
                return clp_attribute.Value
        return ""


class AWSCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(self, clp_res_model: str, clp_resource_attributes: list,
                 shell_helper: ShellHelperObject):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def set_aws_env_vars_based_on_clp(self):
        dec_access_key = ""
        dec_secret_key = ""
        region_flag = False

        for attr in self._clp_resource_attributes:
            dec_access_key = self.get_attribute_value(
                self._clp_res_model, attr, "AWS Access Key ID", self._shell_helper, True)
            dec_secret_key = self.get_attribute_value(
                self._clp_res_model, attr, "AWS Secret Access Key", self._shell_helper, True)
            if self.get_attribute_value(self._clp_res_model, attr, self._shell_helper, "Region"):
                os.environ["AWS_DEFAULT_REGION"] = attr.Value
                region_flag = True
        if not region_flag:
            raise ValueError("Region was not found on AWS Cloud Provider")

        # We must check both keys exist...if not then the EC2 Execution Server profile would be used (Role)
        if dec_access_key and dec_secret_key:
            os.environ["AWS_ACCESS_KEY_ID"] = dec_access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = dec_secret_key


class AzureCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(self, clp_res_model, clp_resource_attributes, shell_helper):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def _set_azure_env_vars_based_on_clp(self):
        for attr in self._clp_resource_attributes:
            attr_val = self.get_attribute_value(self._clp_res_model, attr, self._shell_helper, "Azure Subscription ID")
            if attr_val:
                os.environ["ARM_SUBSCRIPTION_ID"] = attr_val
            attr_val = self.get_attribute_value(self._clp_res_model, attr, self._shell_helper, "Azure Tenant ID")
            if attr_val:
                os.environ["Azure Tenant ID"] = attr_val
            attr_val = self.get_attribute_value(self._clp_res_model, attr, self._shell_helper, "Azure Application ID")
            if attr_val:
                os.environ["ARM_CLIENT_ID"] = attr_val
            attr_val = self.get_attribute_value(self._clp_res_model, attr, self._shell_helper, "Azure Application Key", True)
            if attr_val:
                os.environ["ARM_CLIENT_SECRET"] = attr_val
