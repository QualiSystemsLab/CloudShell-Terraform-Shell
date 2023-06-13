import os
from abc import ABCMeta

import boto3

from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class BaseCloudProviderEnvVarHandler(metaclass=ABCMeta):
    def __init__(self):
        pass

    def set_env_vars_based_on_clp(self):
        raise NotImplementedError()

    @staticmethod
    def does_attribute_match(clp_res_model, clp_attribute, attr_name_to_check) -> bool:
        if (
            f"{clp_res_model}.{clp_attribute.Name}" == attr_name_to_check
            or clp_attribute.Name == attr_name_to_check
            or clp_attribute.Name == f"{clp_res_model}.{attr_name_to_check}"
        ):
            return True
        return False


class AWSCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(
        self,
        clp_res_model: str,
        clp_resource_attributes: list,
        shell_helper: ShellHelperObject,
    ):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def set_env_vars_based_on_clp(self):
        dec_access_key = ""
        dec_secret_key = ""
        token = ""
        iam_role = ""
        region = ""

        for attr in self._clp_resource_attributes:
            if self.does_attribute_match(
                self._clp_res_model, attr, "AWS Access Key ID"
            ):
                dec_access_key = self._shell_helper.api.DecryptPassword(
                    attr.Value
                ).Value
            if self.does_attribute_match(
                self._clp_res_model, attr, "AWS Secret Access Key"
            ):
                dec_secret_key = self._shell_helper.api.DecryptPassword(
                    attr.Value
                ).Value
            if self.does_attribute_match(self._clp_res_model, attr, "Region"):
                region = attr.Value
                os.environ["AWS_DEFAULT_REGION"] = region
            if self.does_attribute_match(
                self._clp_res_model, attr, "Shared VPC Role Arn"
            ):
                iam_role = attr.Value
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

        if dec_access_key and dec_secret_key:
            os.environ["AWS_ACCESS_KEY_ID"] = dec_access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = dec_secret_key
        if token:
            os.environ["AWS_SESSION_TOKEN"] = token

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
        shell_helper: ShellHelperObject,
    ):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

    def set_env_vars_based_on_clp(self):
        for attr in self._clp_resource_attributes:
            if self.does_attribute_match(
                self._clp_res_model, attr, "Azure Subscription ID"
            ):
                os.environ["ARM_SUBSCRIPTION_ID"] = attr.Value
            if self.does_attribute_match(self._clp_res_model, attr, "Azure Tenant ID"):
                os.environ["ARM_TENANT_ID"] = attr.Value
            if self.does_attribute_match(
                self._clp_res_model, attr, "Azure Application ID"
            ):
                os.environ["ARM_CLIENT_ID"] = attr.Value
            if self.does_attribute_match(
                self._clp_res_model, attr, "Azure Application Key"
            ):
                os.environ[
                    "ARM_CLIENT_SECRET"
                ] = self._shell_helper.api.DecryptPassword(attr.Value).Value


class GCPCloudProviderEnvVarHandler(BaseCloudProviderEnvVarHandler):
    def __init__(
        self,
        clp_res_model: str,
        clp_resource_attributes: list,
        shell_helper: ShellHelperObject,
    ):
        BaseCloudProviderEnvVarHandler.__init__(self)
        self._clp_res_model = clp_res_model
        self._clp_resource_attributes = clp_resource_attributes
        self._shell_helper = shell_helper

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
            self._shell_helper.sandbox_messages.write_message(
                "Project ID was not found on GCP Cloud Provider"
            )
