from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from googleapiclient import discovery
# from google.oauth2 import service_account
from google.cloud import storage
import os
import json

from constants import GCP_MODELS, GOOGLE_APPLICATION_CREDENTIALS
from data_model import GcpTfBackend


class GcpTfBackendDriver (ResourceDriverInterface):

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

    # <editor-fold desc="Discovery">

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

        '''
        resource = GcpTfBackend.create_from_context(context)
        resource.vendor = 'specify the shell vendor'
        resource.model = 'specify the shell model'
        port1 = ResourcePort('Port 1')
        port1.ipv4_address = '192.168.10.7'
        resource.add_sub_resource('1', port1)
        return resource.create_autoload_details()
        '''
        with LoggingSessionContext(context) as logger:
            try:
                gcp_service = self._can_conntect_to_gcp(context, logger)
                if not gcp_service:
                    self._raise_and_log(logger, "There was an issue accessing GCP, please check authentication credentials.")
                # raise ValueError("Can't connect to GCP")
            except Exception as e:
                logger.exception(f"There was an issue initialization GCP provider resource. {e}")
            return AutoLoadDetails([], [])

    # </editor-fold>
    # <editor-fold desc="Validate S3 Bucket Exists">
    def _validate_bucket_exists(self, bucket_name: str, context, logger):
        try:
            storage_client = storage.Client()
            get_bucket = storage_client.get_bucket(bucket_name)
            if len(str(get_bucket)) < 0:
                raise ValueError(f"Bucket {bucket_name} not found")
        except Exception as e:
            logger.exception(f"There was an issue accessing the bucket {bucket_name}.{e}")

    def _can_conntect_to_gcp(self, context, logger) -> bool:
        gcp_backend_resource = GcpTfBackend.create_from_context(context)
        project_id = gcp_backend_resource.project
        self._create_gcp_session(context, project_id, logger)
        client = discovery.build('compute', 'v1')
        response = client.healthChecks().list(project=project_id).execute()
        return len(response) > 0

    def get_backend_data(self, context, tf_state_unique_name: str) -> str:
        self._backend_secret_vars = {}

        with LoggingSessionContext(context) as logger:
            gcp_backend_resource = GcpTfBackend.create_from_context(context)
            project_id = gcp_backend_resource.project
            try:
                gcp_service = self._create_gcp_session(context, project_id, logger)
                self._backend_secret_vars = {"credentials": gcp_service}
                os.environ[GOOGLE_APPLICATION_CREDENTIALS] = gcp_service
                os.environ["GOOGLE_PROJECT"] = project_id
            except Exception as e:
                logger.exception("Inputs for Cloud Backend Access missing or incorrect")
            tf_state_file_string = self._generate_state_file_string(gcp_backend_resource, tf_state_unique_name)
            backend_data = {"tf_state_file_string": tf_state_file_string}
            logger.info(f"Returning backend data for creating provider file :\n{backend_data}")
            response = json.dumps({"backend_data": backend_data, "backend_secret_vars": self._backend_secret_vars})
            return response

    def delete_tfstate_file(self, context, tf_state_unique_name: str):
        """Deletes a blob from the bucket."""
        with LoggingSessionContext(context) as logger:
            gcp_backend_resource = GcpTfBackend.create_from_context(context)
            project_id = gcp_backend_resource.project
            try:
                gcp_service = self._create_gcp_session(context, project_id, logger)
                storage_client = storage.Client()
                bucket_name = gcp_backend_resource.bucket_name
                bucket = storage_client.get_bucket(bucket_name)
                """Delete object under folder"""
                blobs = list(bucket.list_blobs(prefix=tf_state_unique_name))
                if len(blobs) == 0 :
                    logger.exception(f"Folder {tf_state_unique_name} not exists.")
                elif len(blobs) > 1 :
                    logger.exception(f"There are more than 1 Folder {tf_state_unique_name} currenlty {len(blobs)} folders exist.")
                else :
                    bucket.delete_blobs(blobs)
                    logger.info(f"Folder {tf_state_unique_name} deleted.")
            except Exception as e:
                logger.exception(f"{tf_state_unique_name} file was not removed from backend provider")

    def _generate_state_file_string(self, gcp_backend_resource: GcpTfBackend, tf_state_unique_name: str):
        tf_state_file_string = f'terraform {{\n\
\tbackend "gcs" {{\n\
\t\tbucket = "{gcp_backend_resource.bucket_name}"\n\
\t\tprefix = "{tf_state_unique_name}"\n\
\t}}\n\
}}'
        return tf_state_file_string

    def _create_gcp_session(self, context, project_id: str, logger):
        if not project_id:
            logger.exception("Project id must be filled")
        api = CloudShellSessionContext(context).get_api()
        gcp_backend_resource = GcpTfBackend.create_from_context(context)
        json_path = gcp_backend_resource.credentials_json_path
        # json_path defines on GCP TF BACKEND RESOURCE
        if json_path:
            if gcp_backend_resource.cloud_provider:
                logger.exception("Only one method of authentication should be filled")
            os.environ[GOOGLE_APPLICATION_CREDENTIALS] = json_path
            os.environ["GOOGLE_PROJECT"] = project_id
        # Keys not defines on GCP TF BACKEND RESOURCE (CLP reference should have been set)
        else:
            # CLP had not been set...
            if not gcp_backend_resource.cloud_provider:
                logger.exception("At least one method of authentication should be filled")

            # Check a correct CLP has been reference
            clp_details = api.GetResourceDetails
            clp_resource_details = self._get_and_validate_clp(clp_details, gcp_backend_resource, logger)
            json_path = self._fill_backend_sercret_vars_data(clp_resource_details)
            os.environ[GOOGLE_APPLICATION_CREDENTIALS] = json_path
            os.environ["GOOGLE_PROJECT"] = project_id
        bucket_name = gcp_backend_resource.bucket_name
        if bucket_name:
            self._validate_bucket_exists(bucket_name, context, logger)
        return json_path

    def _fill_backend_sercret_vars_data(self, clp_resource_details) -> str:
        for attr in clp_resource_details.ResourceAttributes:
            if attr.Name == "Google Cloud Provider.Credentials Json Path":
                clp_json_path = attr.Value
                return clp_json_path

    def _get_and_validate_clp(self, clp_details, gcp_backend_resource: str, logger) -> str:
        clp_details_resource = clp_details(gcp_backend_resource.cloud_provider)
        clp_res_model = clp_details_resource.ResourceModelName
        clpr_res_fam = clp_details_resource.ResourceFamilyName
        if (clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider') or \
                clp_res_model not in GCP_MODELS:
            logger.error(f"Cloud Provider does not have the expected type: {clpr_res_fam}")
            raise ValueError(f"Cloud Provider does not have the expected type:{clpr_res_fam}")
        clp_name = clp_details(clp_details_resource.Name)
        return clp_name

    def _raise_and_log(self, logger, msg):
        logger.exception(msg)
        raise RuntimeError(msg)
