import os
from logging import Logger
from typing import Union

from cloudshell.api.cloudshell_api import ResourceInfo
from cloudshell.iac.terraform.constants import (
    AWS2G_MODEL,
    AZURE2G_MODEL,
    CLP_PROVIDER_MODELS,
    GCP2G_MODEL,
)
from cloudshell.iac.terraform.services.clp_envvar_handler import (
    AWSCloudProviderEnvVarHandler,
    AzureCloudProviderEnvVarHandler,
    BaseCloudProviderEnvVarHandler,
)

from cloudshell.cp.terraform.exceptions import InvalidAppParamValue
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


class GCPCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(
        self, clp_res_model: str, clp_resource_attributes: list, logger: Logger
    ):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._logger = logger

    def set_env_vars_based_on_clp(self):
        project_flag = False
        cred_flag = False
        for attr in self._clp_resource_attributes:
            if self.does_attribute_match(
                self._clp_res_model, attr, "Google Cloud Provider.Credentials Json Path"
            ):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = attr.Value
                cred_flag = True
            if self.does_attribute_match(
                self._clp_res_model, attr, "Google Cloud Provider.project"
            ):
                os.environ["GOOGLE_PROJECT"] = attr.Value
                project_flag = True
        if not cred_flag and not project_flag:
            raise InvalidAppParamValue("Project ID was not found on GCP Cloud Provider")


class CPProviderHandler:
    def __init__(self, resource_config: TerraformResourceConfig, logger: Logger):
        self._logger = logger
        self._resource_config = resource_config

    def initialize_provider(
        self, deploy_app: Union[BaseTFDeployedApp, VMFromTerraformGit]
    ):
        clp_resource_name = (
            deploy_app.cloud_provider or self._resource_config.cloud_provider
        )
        if not clp_resource_name:
            return
        clp_details = self._resource_config.api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName

        clpr_res_fam = clp_details.ResourceFamilyName
        if clpr_res_fam != "Cloud Provider" and clpr_res_fam != "CS_CloudProvider":
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
        self._logger.info(
            "Initializing Environment variables with CloudProvider details"
        )
        clp_resource_attributes = clp_details.ResourceAttributes
        clp_handler = None

        if clp_res_model in [
            AWS2G_MODEL,
        ]:
            clp_handler = AWSCloudProviderEnvVarHandler(
                clp_res_model, clp_resource_attributes, self._resource_config
            )

        elif clp_res_model in [
            AZURE2G_MODEL,
        ]:
            clp_handler = AzureCloudProviderEnvVarHandler(
                clp_res_model, clp_resource_attributes, self._resource_config
            )

        elif clp_res_model in [GCP2G_MODEL]:
            clp_handler = GCPCloudProviderEnvVarHandler(
                clp_res_model, clp_resource_attributes, self._logger
            )

        if clp_handler:
            clp_handler.set_env_vars_based_on_clp()
        else:
            self._logger.error(
                f"Was not able to initialize provider as {clp_res_model} is not a supported model"
            )
            raise ValueError(
                f"Was not able to initialize provider as {clp_res_model} is not a supported model"
            )
