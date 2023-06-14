from __future__ import annotations

from abc import ABC
from logging import Logger
from typing import Dict, Union

import boto3 as boto3

from cloudshell.api.cloudshell_api import CloudShellAPISession, ResourceInfo
from cloudshell.cp.terraform.exceptions import InvalidAppParamValue
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig

from cloudshell.iac.terraform.constants import (
    AWS2G_MODEL,
    AZURE2G_MODEL,
    CLP_PROVIDER_MODELS,
    GCP2G_MODEL,
)


class BaseCloudProviderEnvVarHandler(ABC):
    def get_env_vars_based_on_clp(self):
        pass


class AWSCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(
        self,
        clp_res_model: str,
        clp_resource_attributes: list,
        api: CloudShellAPISession,
    ):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = {
            x.Name.rsplit(".", 1)[-1]: x.Value for x in clp_resource_attributes
        }
        self._api = api

    def get_env_vars_based_on_clp(self):
        token = None
        dec_access_key = self._api.DecryptPassword(
            self._clp_resource_attributes.get("AWS Access Key ID")
        ).Value
        dec_secret_key = self._api.DecryptPassword(
            self._clp_resource_attributes.get("AWS Secret Access Key")
        ).Value
        region = self._clp_resource_attributes.get("Region")
        iam_role = self._clp_resource_attributes.get("Shared VPC Role Arn")
        if not region:
            raise ValueError("Region was not found on AWS Cloud Provider")

        if iam_role:
            default_session = self._create_aws_session(
                access_key_id=dec_access_key,
                secret_access_key=dec_secret_key,
                region=region,
            )
            if not default_session:
                raise ValueError("Could not create AWS Session")

            aws_ec2_session = self._assume_shared_vpc_role(
                aws_session=default_session, shared_vpc_role_arn=iam_role, region=region
            )

            current_credentials = self._get_credentials(session=aws_ec2_session)
            dec_access_key = current_credentials.access_key
            dec_secret_key = current_credentials.secret_key
            token = current_credentials.token

        env_vars = {"REGION": region}
        if dec_access_key and dec_secret_key:
            env_vars["AWS_ACCESS_KEY_ID"] = dec_access_key
            env_vars["AWS_SECRET_ACCESS_KEY"] = dec_secret_key
        if token:
            env_vars["AWS_SESSION_TOKEN"] = token
        return env_vars

    @staticmethod
    def _assume_shared_vpc_role(aws_session, shared_vpc_role_arn, region):
        endpoint_url = f"https://sts.{region}.amazonaws.com"
        sts = aws_session.client("sts", endpoint_url=endpoint_url)

        data = sts.get_caller_identity()
        if data.get("Arn") == shared_vpc_role_arn:
            session = aws_session
        else:
            data = sts.assume_role(
                RoleArn=shared_vpc_role_arn,
                RoleSessionName="CS-SharedVPC-Session",
            )
            credentials = data["Credentials"]
            session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=region,
            )
        return session

    def _get_credentials(self, session):
        credentials = session.get_credentials()
        current_credentials = credentials.get_frozen_credentials()

        return current_credentials

    @staticmethod
    def _create_aws_session(access_key_id, secret_access_key, region):
        if access_key_id or secret_access_key:
            aws_session = boto3.session.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
            )
        else:
            aws_session = boto3.session.Session(region_name=region)

        return aws_session


class AzureCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(
        self,
        clp_res_model: str,
        clp_resource_attributes: list,
        api: CloudShellAPISession,
    ):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = {
            x.Name.rsplit(".", 1)[-1]: x.Value for x in clp_resource_attributes
        }
        self._api = api

    def get_env_vars_based_on_clp(self):
        return {
            "ARM_SUBSCRIPTION_ID": self._clp_resource_attributes.get(
                "Azure Subscription ID"
            ),
            "ARM_TENANT_ID": self._clp_resource_attributes.get("Azure Tenant ID"),
            "ARM_CLIENT_ID": self._clp_resource_attributes.get("Azure Application ID"),
            "ARM_CLIENT_SECRET": self._api.DecryptPassword(
                self._clp_resource_attributes.get("Azure Application Key")
            ).Value,
        }


class GCPCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(self, clp_res_model: str, clp_resource_attributes: list):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = {
            x.Name.rsplit(".", 1)[-1]: x.Value for x in clp_resource_attributes
        }

    def get_env_vars_based_on_clp(self):
        creds = self._clp_resource_attributes.get("Credentials Json Path")
        project = self._clp_resource_attributes.get("project")
        if not creds and not project:
            raise InvalidAppParamValue("Project ID was not found on GCP Cloud Provider")
        return {"GOOGLE_APPLICATION_CREDENTIALS": creds, "GOOGLE_PROJECT": project}


class CPProviderHandler:
    def __init__(self, resource_config: TerraformResourceConfig, logger: Logger):
        self._logger = logger
        self._resource_config = resource_config

    def initialize_provider(
        self, deploy_app: BaseTFDeployedApp | VMFromTerraformGit
    ) -> dict[str, str] | None:
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
                return self._get_cloud_env_vars(clp_details, clp_res_model)
            else:
                self._logger.error(f"{clp_res_model} currently not supported")
                raise ValueError(f"{clp_res_model} currently not supported")

        except Exception as e:
            self._logger.error(f"Error Setting environment variables -> {str(e)}")
            raise

    def _get_cloud_env_vars(
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
                clp_res_model, clp_resource_attributes, self._resource_config.api
            )

        elif clp_res_model in [
            AZURE2G_MODEL,
        ]:
            clp_handler = AzureCloudProviderEnvVarHandler(
                clp_res_model, clp_resource_attributes, self._resource_config.api
            )

        elif clp_res_model in [GCP2G_MODEL]:
            clp_handler = GCPCloudProviderEnvVarHandler(
                clp_res_model, clp_resource_attributes
            )

        if clp_handler:
            return clp_handler.get_env_vars_based_on_clp()
        else:
            self._logger.error(
                f"Was not able to initialize provider as {clp_res_model} "
                f"is not a supported model"
            )
            raise ValueError(
                f"Was not able to initialize provider as {clp_res_model} "
                f"is not a supported model"
            )
