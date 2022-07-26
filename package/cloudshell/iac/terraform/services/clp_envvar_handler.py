import os
from abc import ABCMeta
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class BaseCloudProviderEnvVarHandler(metaclass=ABCMeta):
    def __init__(self):
        pass

    def set_env_vars_based_on_clp(self):
        raise NotImplementedError()

    @staticmethod
    def does_attribute_match(clp_res_model, clp_attribute, attr_name_to_check) -> bool:
        if f"{clp_res_model}.{clp_attribute.Name}" == attr_name_to_check or clp_attribute.Name == attr_name_to_check \
                or clp_attribute.Name == f"{clp_res_model}.{attr_name_to_check}":
            return True
        return False


class AWSCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(self, clp_res_model: str, clp_resource_attributes: list, shell_helper: ShellHelperObject):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def set_env_vars_based_on_clp(self):
        dec_access_key = ""
        dec_secret_key = ""
        region_flag = False

        for attr in self._clp_resource_attributes:
            if self.does_attribute_match(self._clp_res_model, attr, "AWS Access Key ID"):
                dec_access_key = self._shell_helper.api.DecryptPassword(attr.Value).Value
            if self.does_attribute_match(self._clp_res_model, attr, "AWS Secret Access Key"):
                dec_secret_key = self._shell_helper.api.DecryptPassword(attr.Value).Value
            if self.does_attribute_match(self._clp_res_model, attr, "Region"):
                os.environ["AWS_DEFAULT_REGION"] = attr.Value
                region_flag = True
        if not region_flag:
            raise ValueError("Region was not found on AWS Cloud Provider")

        # We must check both keys exist...if not then the EC2 Execution Server profile would be used (Role)
        if dec_access_key and dec_secret_key:
            os.environ["AWS_ACCESS_KEY_ID"] = dec_access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = dec_secret_key


class AzureCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(self, clp_res_model: str, clp_resource_attributes: list, shell_helper: ShellHelperObject):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def set_env_vars_based_on_clp(self):
        for attr in self._clp_resource_attributes:
            if self.does_attribute_match(self._clp_res_model, attr, "Azure Subscription ID"):
                os.environ["ARM_SUBSCRIPTION_ID"] = attr.Value
            if self.does_attribute_match(self._clp_res_model, attr, "Azure Tenant ID"):
                os.environ["ARM_TENANT_ID"] = attr.Value
            if self.does_attribute_match(self._clp_res_model, attr, "Azure Application ID"):
                os.environ["ARM_CLIENT_ID"] = attr.Value
            if self.does_attribute_match(self._clp_res_model, attr, "Azure Application Key"):
                os.environ["ARM_CLIENT_SECRET"] = self._shell_helper.api.DecryptPassword(attr.Value).Value


class GCPCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(self, clp_res_model: str, clp_resource_attributes: list, shell_helper: ShellHelperObject):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def set_env_vars_based_on_clp(self):
        project_flag = False
        cred_flag = False
        for attr in self._clp_resource_attributes:
            if self.does_attribute_match(self._clp_res_model, attr, "Google Cloud Provider.Credentials Json Path"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = attr.Value
                cred_flag = True
            if self.does_attribute_match(self._clp_res_model, attr, "Google Cloud Provider.project"):
                os.environ["GOOGLE_PROJECT"] = attr.Value
                project_flag = True
        if not cred_flag and not project_flag:
            self._shell_helper.sandbox_messages.write_message("Project ID was not found on GCP Cloud Provider")
