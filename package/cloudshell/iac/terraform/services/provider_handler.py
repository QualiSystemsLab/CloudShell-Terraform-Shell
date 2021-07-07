import os
from logging import Logger

from cloudshell.iac.terraform.constants import AZURE2G_MODEL
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class ProviderHandler(object):
    def __init__(self, logger: Logger):
        self.logger = logger

    @staticmethod
    def initialize_provider(shell_helper: ShellHelperObject):
        clp_resource_name = shell_helper.tf_service.cloud_provider
        if not clp_resource_name:
            return
        clp_res_model = shell_helper.api.GetResourceDetails(clp_resource_name).ResourceModelName
        clpr_res_fam = shell_helper.api.GetResourceDetails(clp_resource_name).ResourceFamilyName

        if clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider':
            shell_helper.logger.error(f"{clpr_res_fam} currently not supported")
            raise ValueError(f"{clpr_res_fam} currently not supported")

        try:
            if clp_res_model == 'Microsoft Azure' or clp_res_model == AZURE2G_MODEL:
                shell_helper.sandbox_messages.write_message("initializing provider...")
                shell_helper.logger.info("Initializing Environment variables with CloudProvider details")
                clp_resource_attributes = shell_helper.api.GetResourceDetails(clp_resource_name).ResourceAttributes

                azure_attr_name_prefix = ""
                if clp_res_model == AZURE2G_MODEL:
                    azure_attr_name_prefix = AZURE2G_MODEL + "."

                for attr in clp_resource_attributes:
                    if attr.Name == azure_attr_name_prefix+"Azure Subscription ID":
                        os.environ["ARM_SUBSCRIPTION_ID"] = attr.Value
                    if attr.Name == azure_attr_name_prefix+"Azure Tenant ID":
                        os.environ["ARM_TENANT_ID"] = attr.Value
                    if attr.Name== azure_attr_name_prefix+"Azure Application ID":
                        os.environ["ARM_CLIENT_ID"] = attr.Value
                    if attr.Name == azure_attr_name_prefix+"Azure Application Key":
                        dec_client_secret = shell_helper.api.DecryptPassword(attr.Value).Value
                        os.environ["ARM_CLIENT_SECRET"] = dec_client_secret
            else:
                shell_helper.logger.error(f"{clp_res_model} currently not supported")
                raise ValueError(f"{clp_res_model} currently not supported")

        except Exception as e:
            shell_helper.logger.error(f"Error Setting environment variables -> {str(e)}")
            raise
