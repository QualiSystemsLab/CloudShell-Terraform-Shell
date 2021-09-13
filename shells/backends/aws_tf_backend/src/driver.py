from botocore.exceptions import ClientError
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext
#from data_model import *  # run 'shellfoundry generate' to generate data model classes
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
import boto3

from aws_tf_backend.src.constants import AWS_MODELS, AWS2G_MODEL
from azure_tf_backend.src.constants import ACCESS_KEY_ATTRIBUTE
from data_model import *


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

        return AutoLoadDetails([], [])


    def _validate_bucket_exists(self, context):
        with LoggingSessionContext(context) as logger:
            aws_backend_resource = AwsTfBackend.create_from_context(context)
            try:
                api = CloudShellSessionContext(context).get_api()
                access_key = api.DecryptPassword(aws_backend_resource.access_key).Value
                secret_key = api.DecryptPassword(aws_backend_resource.secret_key).Value
                bucket_name = aws_backend_resource.bucket_name

                self._validate_attributes(aws_backend_resource, bucket_name, logger)
                if access_key and secret_key:
                    if aws_backend_resource.cloud_provider:
                        self._handle_exception_logging(logger, "Only one method of authentication should be filled")

                    aws_session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
                else:
                    if not aws_backend_resource.cloud_provider:
                        self._handle_exception_logging(logger, "At least one method of authentication should be filled")

                    clp_details = self._validate_clp(api, aws_backend_resource, logger)

                    aws_model_prefix = ""
                    if clp_details.ResourceModelName == AWS2G_MODEL:
                        aws_model_prefix = AWS2G_MODEL + "."
                    access_key = self._get_attrbiute_value_from_clp(clp_details.ResourceAttributes, ACCESS_KEY_ATTRIBUTE)
                    aws_session = boto3.Session()

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

    def _get_attrbiute_value_from_clp(self,attributes , model_prefix, attribute_name):
        for attribute in attributes:
            if attribute.name == f"{model_prefix} + {}attribute_name}:


    def _validate_attributes(self, aws_backend_resource, bucket_name, logger):

        if not aws_backend_resource.region_name:
            self._handle_exception_logging(logger, "Region should be filled")
        if not bucket_name:
            self._handle_exception_logging(logger, "Bucket Name be filled")

    def _handle_exception_logging(self, logger, msg):
        logger.exception(msg)
        raise ValueError(msg)

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

    def orchestration_save(self, context, cancellation_context, mode, custom_params):
      """
      Saves the Shell state and returns a description of the saved artifacts and information
      This command is intended for API use only by sandbox orchestration scripts to implement
      a save and restore workflow
      :param ResourceCommandContext context: the context object containing resource and reservation info
      :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
      :param str mode: Snapshot save mode, can be one of two values 'shallow' (default) or 'deep'
      :param str custom_params: Set of custom parameters for the save operation
      :return: SavedResults serialized as JSON
      :rtype: OrchestrationSaveResult
      """

      # See below an example implementation, here we use jsonpickle for serialization,
      # to use this sample, you'll need to add jsonpickle to your requirements.txt file
      # The JSON schema is defined at:
      # https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/saved_artifact_info.schema.json
      # You can find more information and examples examples in the spec document at
      # https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/save%20%26%20restore%20standard.md
      '''
            # By convention, all dates should be UTC
            created_date = datetime.datetime.utcnow()

            # This can be any unique identifier which can later be used to retrieve the artifact
            # such as filepath etc.

            # By convention, all dates should be UTC
            created_date = datetime.datetime.utcnow()

            # This can be any unique identifier which can later be used to retrieve the artifact
            # such as filepath etc.
            identifier = created_date.strftime('%y_%m_%d %H_%M_%S_%f')

            orchestration_saved_artifact = OrchestrationSavedArtifact('REPLACE_WITH_ARTIFACT_TYPE', identifier)

            saved_artifacts_info = OrchestrationSavedArtifactInfo(
                resource_name="some_resource",
                created_date=created_date,
                restore_rules=OrchestrationRestoreRules(requires_same_resource=True),
                saved_artifact=orchestration_saved_artifact)

            return OrchestrationSaveResult(saved_artifacts_info)
      '''
      pass

    def orchestration_restore(self, context, cancellation_context, saved_artifact_info, custom_params):
        """
        Restores a saved artifact previously saved by this Shell driver using the orchestration_save function
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str saved_artifact_info: A JSON string representing the state to restore including saved artifacts and info
        :param str custom_params: Set of custom parameters for the restore operation
        :return: None
        """
        '''
        # The saved_details JSON will be defined according to the JSON Schema and is the same object returned via the
        # orchestration save function.
        # Example input:
        # {
        #     "saved_artifact": {
        #      "artifact_type": "REPLACE_WITH_ARTIFACT_TYPE",
        #      "identifier": "16_08_09 11_21_35_657000"
        #     },
        #     "resource_name": "some_resource",
        #     "restore_rules": {
        #      "requires_same_resource": true
        #     },
        #     "created_date": "2016-08-09T11:21:35.657000"
        #    }

        # The example code below just parses and prints the saved artifact identifier
        saved_details_object = json.loads(saved_details)
        return saved_details_object[u'saved_artifact'][u'identifier']
        '''
        pass

