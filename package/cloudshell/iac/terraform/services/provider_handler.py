from logging import Logger

from cloudshell.api.cloudshell_api import ResourceInfo

from cloudshell.iac.terraform.constants import AZURE2G_MODEL, ATTRIBUTE_NAMES, AWS2G_MODEL, CLP_PROVIDER_MODELS, \
    AWS1G_MODEL, AZURE1G_MODEL, GCP2G_MODEL
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.clp_envvar_handler import AWSCloudProviderEnvVarHandler, \
    AzureCloudProviderEnvVarHandler, GCPCloudProviderEnvVarHandler


class ProviderHandler(object):
    def __init__(self, logger: Logger):
        self.logger = logger

    def initialize_provider(self, shell_helper: ShellHelperObject):
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
                self._set_cloud_env_vars(clp_details, clp_res_model, shell_helper)
            else:
                shell_helper.logger.error(f"{clp_res_model} currently not supported")
                raise ValueError(f"{clp_res_model} currently not supported")

        except Exception as e:
            shell_helper.logger.error(f"Error Setting environment variables -> {str(e)}")
            raise

    def _set_cloud_env_vars(
            self,
            clp_details: ResourceInfo,
            clp_res_model: str,
            shell_helper: ShellHelperObject,
    ):
        shell_helper.sandbox_messages.write_message("initializing provider...")
        shell_helper.logger.info("Initializing Environment variables with CloudProvider details")
        clp_resource_attributes = clp_details.ResourceAttributes
        clp_handler = None

        if clp_res_model in [AWS1G_MODEL, AWS2G_MODEL]:
            clp_handler = AWSCloudProviderEnvVarHandler(clp_res_model, clp_resource_attributes, shell_helper)

        elif clp_res_model in [AZURE1G_MODEL, AZURE2G_MODEL]:
            clp_handler = AzureCloudProviderEnvVarHandler(clp_res_model, clp_resource_attributes, shell_helper)

        elif clp_res_model in [GCP2G_MODEL]:
            clp_handler = GCPCloudProviderEnvVarHandler(clp_res_model, clp_resource_attributes, shell_helper)

        if clp_handler:
            clp_handler.set_env_vars_based_on_clp()
        else:
            self.logger.error(f"Was not able to initialize provider as {clp_res_model} is not a supported model")
            raise ValueError(f"Was not able to initialize provider as {clp_res_model} is not a supported model")
