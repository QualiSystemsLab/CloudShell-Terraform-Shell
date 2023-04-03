from logging import Logger

from cloudshell.api.cloudshell_api import ResourceInfo

from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.iac.terraform.constants import (
    AZURE2G_MODEL,
    AWS2G_MODEL,
    CLP_PROVIDER_MODELS,
    GCP2G_MODEL
)
from cloudshell.iac.terraform.services.clp_envvar_handler import (
    AWSCloudProviderEnvVarHandler,
    AzureCloudProviderEnvVarHandler,
    GCPCloudProviderEnvVarHandler
)


class CPProviderHandler(object):
    def __init__(self, resource_config: TerraformResourceConfig, logger: Logger):
        self._logger = logger
        self._resource_config = resource_config

    def initialize_provider(self, deploy_app: VMFromTerraformGit):
        clp_resource_name = deploy_app.cloud_provider or self._resource_config.cloud_provider
        if not clp_resource_name:
            return
        clp_details = self._resource_config.api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName

        clpr_res_fam = clp_details.ResourceFamilyName
        if clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider':
            self._logger.error(f"{clpr_res_fam} currently not supported")
            raise ValueError(f"{clpr_res_fam} currently not supported")

        try:
            if clp_res_model in CLP_PROVIDER_MODELS:
                self._set_cloud_env_vars(clp_details, clp_res_model)
            else:
                self._logger.error(f"{clp_res_model} currently not supported")
                raise ValueError(f"{clp_res_model} currently not supported")

        except Exception as e:
            self._logger.error(f"Error Setting environment variables -> {str(e)}")
            raise

    def _set_cloud_env_vars(
            self,
            clp_details: ResourceInfo,
            clp_res_model: str,
    ):
        self._logger.info("Initializing Environment variables with CloudProvider "
                         "details")
        clp_resource_attributes = clp_details.ResourceAttributes
        clp_handler = None

        if clp_res_model in [AWS2G_MODEL, ]:
            clp_handler = AWSCloudProviderEnvVarHandler(clp_res_model, clp_resource_attributes, self._resource_config.api)

        elif clp_res_model in [AZURE2G_MODEL, ]:
            clp_handler = AzureCloudProviderEnvVarHandler(clp_res_model,
                                                          clp_resource_attributes,
                                                          self._resource_config.api)

        elif clp_res_model in [GCP2G_MODEL]:
            clp_handler = GCPCloudProviderEnvVarHandler(clp_res_model, clp_resource_attributes)

        if clp_handler:
            clp_handler.set_env_vars_based_on_clp()
        else:
            self._logger.error(f"Was not able to initialize provider as {clp_res_model} is not a supported model")
            raise ValueError(f"Was not able to initialize provider as {clp_res_model} is not a supported model")
