import os
from logging import Logger

from cloudshell.api.cloudshell_api import ResourceInfo

from cloudshell.iac.terraform.constants import AZURE2G_MODEL, ATTRIBUTE_NAMES, AWS2G_MODEL, CLP_PROVIDER_MODELS
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class ProviderHandler(object):
    def __init__(self, logger: Logger):
        self.logger = logger

    @staticmethod
    def initialize_provider(shell_helper: ShellHelperObject):
        clp_resource_name = shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.CLOUD_PROVIDER)
        if not clp_resource_name:
            return
        clp_details = shell_helper.api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName

        clpr_res_fam = clp_details.ResourceFamilyName
        if clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider':
            shell_helper.logger.error(f"{clpr_res_fam} currently not supported")
            raise ValueError(f"{clpr_res_fam} currently not supported")

        try:
            if clp_res_model in CLP_PROVIDER_MODELS:
                ProviderHandler._set_cloud_env_vars(
                    clp_details,
                    clp_res_model,
                    shell_helper
                )
            else:
                shell_helper.logger.error(f"{clp_res_model} currently not supported")
                raise ValueError(f"{clp_res_model} currently not supported")

        except Exception as e:
            shell_helper.logger.error(f"Error Setting environment variables -> {str(e)}")
            raise

    @staticmethod
    def _set_cloud_env_vars(
            clp_details: ResourceInfo,
            clp_res_model: str,
            shell_helper: ShellHelperObject,
    ):
        shell_helper.sandbox_messages.write_message("initializing provider...")
        shell_helper.logger.info("Initializing Environment variables with CloudProvider details")
        clp_resource_attributes = clp_details.ResourceAttributes

        cloud_attr_name_prefix = ""
        if clp_res_model in [AZURE2G_MODEL, AWS2G_MODEL]:
            cloud_attr_name_prefix = clp_res_model + "."

        if clp_res_model in ['AWS EC2', AWS2G_MODEL]:
            ProviderHandler._set_aws_env_vars_based_on_clp(
                cloud_attr_name_prefix, clp_resource_attributes, shell_helper)
        elif clp_res_model in ['Microsoft Azure', AZURE2G_MODEL]:
            ProviderHandler._set_azure_env_vars_based_on_clp(
                cloud_attr_name_prefix, clp_resource_attributes, shell_helper)

    @staticmethod
    def _set_azure_env_vars_based_on_clp(azure_attr_name_prefix, clp_resource_attributes, shell_helper):
        for attr in clp_resource_attributes:
            if attr.Name == azure_attr_name_prefix + "Azure Subscription ID":
                os.environ["ARM_SUBSCRIPTION_ID"] = attr.Value
            if attr.Name == azure_attr_name_prefix + "Azure Tenant ID":
                os.environ["ARM_TENANT_ID"] = attr.Value
            if attr.Name == azure_attr_name_prefix + "Azure Application ID":
                os.environ["ARM_CLIENT_ID"] = attr.Value
            if attr.Name == azure_attr_name_prefix + "Azure Application Key":
                dec_client_secret = shell_helper.api.DecryptPassword(attr.Value).Value
                os.environ["ARM_CLIENT_SECRET"] = dec_client_secret

    @staticmethod
    def _set_aws_env_vars_based_on_clp(aws_attr_name_prefix, clp_resource_attributes, shell_helper):
        dec_access_key = ""
        dec_secret_key = ""
        region_flag = False

        for attr in clp_resource_attributes:
            if attr.Name == aws_attr_name_prefix + "AWS Access Key ID":
                dec_access_key = shell_helper.api.DecryptPassword(attr.Value).Value
            if attr.Name == aws_attr_name_prefix + "AWS Secret Access Key":
                dec_secret_key = shell_helper.api.DecryptPassword(attr.Value).Value
            if attr.Name == aws_attr_name_prefix + "Region":
                os.environ["AWS_DEFAULT_REGION"] = attr.Value
                region_flag = True
        if not region_flag:
            raise ValueError("Region was not found on AWS Cloud Provider")

        # We must check both keys exist...if not then the EC2 Execution Server profile would be used (Role)
        if dec_access_key and dec_secret_key:
            os.environ["AWS_ACCESS_KEY_ID"] = dec_access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = dec_secret_key
