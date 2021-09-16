import json

from botocore.exceptions import ClientError
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import AutoLoadDetails
# from data_model import *  # run 'shellfoundry generate' to generate data model classes
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
import boto3

from aws_tf_backend.src.constants import AWS_MODELS, AWS2G_MODEL
from azure_tf_backend.src.constants import ACCESS_KEY_ATTRIBUTE
from data_model import AwsTfBackend


class AwsTfBackendDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        # See below some example code demonstrating how to return the resource structure and attributes
        # In real life, this code will be preceded by SNMP/other calls to the resource details and will not be static
        # run 'shellfoundry generate' in order to create classes that represent your data model
        self._validate_bucket_exists(context)
        return AutoLoadDetails([], [])

    # <editor-fold desc="Exposed shell commands get backend data and delete tfstate_File">
    def get_backend_data(self, context, tf_state_unique_name: str) -> str:
        self._backend_secret_vars = {}

        with LoggingSessionContext(context) as logger:
            aws_backend_resource = AwsTfBackend.create_from_context(context)
            tf_state_file_string = self._generate_state_file_string(aws_backend_resource, tf_state_unique_name)

            backend_data = {"tf_state_file_string": tf_state_file_string}
            try:
                api = CloudShellSessionContext(context).get_api()
                access_key = api.DecryptPassword(aws_backend_resource.access_key).Value
                secret_key = api.DecryptPassword(aws_backend_resource.secret_key).Value

                if access_key and secret_key:
                    self._backend_secret_vars = {"access_key": access_key, "secret_key": secret_key}
                else:
                    if aws_backend_resource.cloud_provider:
                        clp_details = self._validate_clp(api, aws_backend_resource, logger)

                        aws_model_prefix = ""
                        if clp_details.ResourceModelName == AWS2G_MODEL:
                            aws_model_prefix = AWS2G_MODEL + "."
                        self._fill_backend_sercret_vars_data(clp_details, aws_model_prefix)

            except Exception as e:
                self._handle_exception_logging(logger, "Inputs for Cloud Backend Access missing or incorrect")

            logger.info(f"Returning backend data for creating provider file :\n{backend_data}")
            response = json.dumps({"backend_data": backend_data, "backend_secret_vars": self._backend_secret_vars})
            return response

    def delete_tfstate_file(self, context, tf_state_unique_name: str):
        with LoggingSessionContext(context) as logger:
            aws_backend_resource = AwsTfBackend.create_from_context(context)
            try:
                api = CloudShellSessionContext(context).get_api()
                access_key = api.DecryptPassword(aws_backend_resource.access_key).Value
                secret_key = api.DecryptPassword(aws_backend_resource.secret_key).Value
                bucket_name = aws_backend_resource.bucket_name

                self._validate_attributes(aws_backend_resource, bucket_name, logger)

                aws_session = self._create_aws_session(access_key, api, aws_backend_resource, logger, secret_key)
                aws_session.resource('s3').meta.client.delete_object(Bucket=bucket_name, Key=tf_state_unique_name)
            except Exception as e:
                raise ValueError(f"{tf_state_unique_name} file was not removed from backend provider")
    # </editor-fold>

    def _fill_backend_sercret_vars_data(self, clp_details, aws_model_prefix) -> None:
        self._backend_secret_vars = {}
        access_key = self._get_attrbiute_value_from_clp(
            clp_details.ResourceAttributes, aws_model_prefix, ACCESS_KEY_ATTRIBUTE),
        secret_key = self._get_attrbiute_value_from_clp(
            clp_details.ResourceAttributes, aws_model_prefix, ACCESS_KEY_ATTRIBUTE)
        if access_key and secret_key:
            self._backend_secret_vars = {"access_key": access_key, "secret_key": secret_key}

    def _generate_state_file_string(self, aws_backend_resource: AwsTfBackend, tf_state_unique_name: str):
        tf_state_file_string = f'terraform {{\n\
\tbackend "s3" {{\n\
\t\tbucket = "{aws_backend_resource.bucket_name}"\n\
\t\tkey    = "{tf_state_unique_name}"\n\
\t\tregion = "{aws_backend_resource.region_name}"\n\
\t}}\n\
}}'
        return tf_state_file_string

    # <editor-fold desc="Validate S3 Bucket Exists">
    def _validate_bucket_exists(self, context):
        with LoggingSessionContext(context) as logger:
            aws_backend_resource = AwsTfBackend.create_from_context(context)
            try:
                api = CloudShellSessionContext(context).get_api()
                access_key = api.DecryptPassword(aws_backend_resource.access_key).Value
                secret_key = api.DecryptPassword(aws_backend_resource.secret_key).Value
                bucket_name = aws_backend_resource.bucket_name

                self._validate_attributes(aws_backend_resource, bucket_name, logger)

                aws_session = self._create_aws_session(access_key, api, aws_backend_resource, logger, secret_key)

                bucket_data = aws_session.resource('s3').meta.client.head_bucket(Bucket=bucket_name)

            except ClientError as client_exception:
                if client_exception.response['Error']['Code'] == '403':
                    self._handle_exception_logging(logger, "Access to bucket denied (possibly wrong keys)")
                if client_exception.response['Error']['Code'] == '404':
                    self._handle_exception_logging(logger, "Bucket was not found")
                self._handle_exception_logging(logger, f"There was an issue accessing the bucket. Error code = "
                                                       f"{client_exception.response['Error']['Code']}")
            except Exception as e:
                self._handle_exception_logging(logger, "There was an issue accessing the bucket.")

    def _create_aws_session(self, access_key, api, aws_backend_resource, logger, secret_key):
        # Keys defines on AWS TF BACKEND RESOURCE
        if access_key and secret_key:
            if aws_backend_resource.cloud_provider:
                self._handle_exception_logging(logger, "Only one method of authentication should be filled")

            aws_session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)

        # Keys not defines on AWS TF BACKEND RESOURCE (CLP reference should have been set)
        else:
            # CLP had not been set...
            if not aws_backend_resource.cloud_provider:
                self._handle_exception_logging(logger, "At least one method of authentication should be filled")

            # Check a correct CLP has been reference and get an AWS session based of its attributes
            clp_details = self._validate_clp(api, aws_backend_resource, logger)
            aws_session = self._get_aws_session_based_on_clp(clp_details)
        return aws_session

    def _get_aws_session_based_on_clp(self, clp_details):
        aws_model_prefix = ""
        if clp_details.ResourceModelName == AWS2G_MODEL:
            aws_model_prefix = AWS2G_MODEL + "."
        access_key = self._get_attrbiute_value_from_clp(
            clp_details.ResourceAttributes, aws_model_prefix, ACCESS_KEY_ATTRIBUTE)
        secret_key = self._get_attrbiute_value_from_clp(
            clp_details.ResourceAttributes, aws_model_prefix, ACCESS_KEY_ATTRIBUTE)
        if access_key and secret_key:
            aws_session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        else:
            aws_session = boto3.Session()
        return aws_session

    def _get_attrbiute_value_from_clp(self, attributes, model_prefix, attribute_name) -> str:
        for attribute in attributes:
            if attribute.name == f"{model_prefix} + {attribute_name}":
                return attribute.value
        return ""

    def _validate_attributes(self, aws_backend_resource, bucket_name, logger):

        if not aws_backend_resource.region_name:
            self._handle_exception_logging(logger, "Region should be filled")
        if not bucket_name:
            self._handle_exception_logging(logger, "Bucket Name be filled")

    def _validate_clp(self, api, aws_backend_resource, logger):
        clp_resource_name = aws_backend_resource.cloud_provider
        clp_details = api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName
        clpr_res_fam = clp_details.ResourceFamilyName
        if (clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider') or \
                clp_res_model not in AWS_MODELS:
            logger.error(f"Cloud Provider does not have the expected type: {clpr_res_fam}")
            raise ValueError(f"Cloud Provider does not have the expected type:{clpr_res_fam}")
        return clp_details

    def _handle_exception_logging(self, logger, msg):
        logger.exception(msg)
        raise ValueError(msg)
    # </editor-fold>
