from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext    
#from data_model import *  # run 'shellfoundry generate' to generate data model classes

from googleapiclient import discovery
from google.oauth2 import service_account
from google.cloud import storage
import os
import json

from constants import GCP_MODELS, GCP1G_MODEL, CREDENTIALS_JSON_PATH, AUTH_URI, TOKEN_URI, TYPE_ACCOUNT, DYNAMIC_JSON, GOOGLE_APPLICATION_CREDENTIALS
from data_model import GcpTfBackend
# from contextlib import redirect_stdout

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
        logger = LoggingSessionContext(context)
        gcp_service = self._can_conntect_to_gcp(context, logger)
        if not gcp_service:
            raise ValueError("Can't connect to GCP")
        return AutoLoadDetails([], [])
        os.remove(DYNAMIC_JSON)

    # </editor-fold>

    # <editor-fold desc="Validate S3 Bucket Exists">
    def _validate_bucket_exists(self, bucket_name, context, logger):
        # with LoggingSessionContext(context) as logger:
        try:
            storage_client = storage.Client()
            get_bucket = storage_client.get_bucket(bucket_name)
            if len(str(get_bucket)) < 0:
                raise ValueError(f"Bucket {bucket_name} not found")  
        except Exception as e:
            self._raise_and_log(logger, f"There was an issue accessing the bucket.{e}")        

    def _can_conntect_to_gcp(self, context, logger):
        gcp_backend_resource = GcpTfBackend.create_from_context(context)
        project_id = gcp_backend_resource.project
        create_session=self._create_gcp_session(context, project_id, logger)
        client = discovery.build('compute', 'v1')
        response = client.healthChecks().list(project=project_id).execute()
        return len(response) > 0

    def _generate_state_file_string(self, gcp_backend_resource: GcpTfBackend):
        tf_state_file_string = f'terraform {{\n\
\tbackend "gcs" {{\n\
\t\tbucket = "{gcp_backend_resource.bucket_name}"\n\
\t\tprefix = "{gcp_backend_resource.prefix}"\n\
\t}}\n\
}}'
        return tf_state_file_string


    def _create_gcp_session(self, context, project_id, logger):
        # with LoggingSessionContext(context) as logger:
        api = CloudShellSessionContext(context).get_api()
        gcp_backend_resource = GcpTfBackend.create_from_context(context)
        try:
            private_key = api.DecryptPassword(gcp_backend_resource.private_key).Value.replace("\\n", "\n")
            email = api.DecryptPassword(gcp_backend_resource.client_email).Value
            if not project_id:
                self._raise_and_log(logger, "Project id must be filled")
            # Key and email defines on GCP TF BACKEND RESOURCE
            if private_key and email:
                if gcp_backend_resource.cloud_provider:
                    self._raise_and_log(logger, "Only one method of authentication should be filled")
                with open(DYNAMIC_JSON, 'w', encoding='utf-8') as f:
                    json.dump({ "type": TYPE_ACCOUNT, "project_id": project_id, "private_key": private_key, "client_email": email,"auth_uri": AUTH_URI, "token_uri": TOKEN_URI }, f, ensure_ascii=False, indent=4)
                os.environ[GOOGLE_APPLICATION_CREDENTIALS] = DYNAMIC_JSON
            # Keys not defines on GCP TF BACKEND RESOURCE (CLP reference should have been set)
            else:
                # CLP had not been set...
                if not gcp_backend_resource.cloud_provider:
                    self._raise_and_log(logger, "At least one method of authentication should be filled")
                # Check a correct CLP has been reference
                clp_details = api.GetResourceDetails
                clp_resource_details = self._get_and_validate_clp(clp_details, gcp_backend_resource, logger)
                if clp_resource_details.ResourceModelName == GCP1G_MODEL:
                    myactual=clp_details(clp_resource_details.Name)
                    clp_json_path = self._fill_backend_sercret_vars_data(myactual, GCP1G_MODEL)
                    os.environ[GOOGLE_APPLICATION_CREDENTIALS] = clp_json_path
        except Exception as e:
            self._raise_and_log(logger, f"There was an issue accessing GCP. {e}")
        bucket_name = gcp_backend_resource.bucket_name
        if bucket_name:      
            self._validate_bucket_exists(bucket_name, context)

    def _fill_backend_sercret_vars_data(self, myactual, clp):
        for attr in  myactual.ResourceAttributes:
            if attr.Name == "Google Cloud Provider.Credentials Json Path":
                clp_json_path = attr.Value
                return clp_json_path


    def _get_and_validate_clp(self, clp_details, gcp_backend_resource, logger):
        # clp_resource_name = gcp_backend_resource.cloud_provider
        clp_details_resource_name = clp_details(gcp_backend_resource.cloud_provider)
        clp_res_model = clp_details_resource_name.ResourceModelName
        clpr_res_fam = clp_details_resource_name.ResourceFamilyName
        if (clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider') or \
                clp_res_model not in GCP_MODELS:
            logger.error(f"Cloud Provider does not have the expected type: {clpr_res_fam}")
            raise ValueError(f"Cloud Provider does not have the expected type:{clpr_res_fam}")
        return clp_details_resource_name

    def _raise_and_log(self, logger, msg):
        logger.exception(msg)
        raise ValueError(msg)