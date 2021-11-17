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
        gcp_service = self._can_connect(context)
        if not gcp_service:
            raise ValueError("Can't connect to GCP")
        return AutoLoadDetails([], [])
        os.remove(DYNAMIC_JSON)

    # </editor-fold>

    # <editor-fold desc="Validate S3 Bucket Exists">
    def _validate_bucket_exists(self, bucket_name, context):
        with LoggingSessionContext(context) as logger:
            try:
                storage_client = storage.Client()
                get_bucket = storage_client.get_bucket(bucket_name)
                if len(str(get_bucket)) < 0:
                    raise ValueError('Could not connect: Check credentials')  
            except Exception as e:
                self._handle_exception_logging(logger, f"There was an issue accessing the bucket.{e}")        

    def _can_connect(self, context):
        # api = CloudShellSessionContext(context).get_api()
        gcp_backend_resource = GcpTfBackend.create_from_context(context)
        project_id = gcp_backend_resource.project
        create_session=self._create_gcp_session(context, project=project_id)

        client = discovery.build('compute', 'v1')
        response = client.healthChecks().list(project=project_id).execute()
        # return response
        return len(response) > 0

    def _generate_state_file_string(self, gcp_backend_resource: GcpTfBackend):

        tf_state_file_string = f'terraform {{\n\
\tbackend "gcs" {{\n\
\t\tbucket = "{gcp_backend_resource.bucket_name}"\n\
\t\tprefix = "{gcp_backend_resource.prefix}"\n\
\t}}\n\
}}'
        return tf_state_file_string


    def _create_gcp_session(self, context, project):
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()
            gcp_backend_resource = GcpTfBackend.create_from_context(context)
            try:
                private_key = api.DecryptPassword(gcp_backend_resource.private_key).Value.replace("\\n", "\n")
                email = api.DecryptPassword(gcp_backend_resource.client_email).Value
                project_id = project
                if not project_id:
                    self._handle_exception_logging(logger, "Project id must be filled")
                # Keys defines on AWS TF BACKEND RESOURCE
                if private_key and email:
                    if gcp_backend_resource.cloud_provider:
                        self._handle_exception_logging(logger, "Only one method of authentication should be filled")
                    # bucket_name = gcp_backend_resource.bucket_name
                    with open(DYNAMIC_JSON, 'w', encoding='utf-8') as f:
                        json.dump({ "type": TYPE_ACCOUNT, "project_id": project_id, "private_key": private_key, "client_email": email,"auth_uri": AUTH_URI, "token_uri": TOKEN_URI }, f, ensure_ascii=False, indent=4)
                    os.environ[GOOGLE_APPLICATION_CREDENTIALS] = DYNAMIC_JSON
                # Keys not defines on AWS TF BACKEND RESOURCE (CLP reference should have been set)
                else:
                    # CLP had not been set...
                    if not gcp_backend_resource.cloud_provider:
                        self._handle_exception_logging(logger, "At least one method of authentication should be filled")
                    # Check a correct CLP has been reference
                    # clp_details = api.GetResourceDetails(aws_backend_resource.cloud_provider)
                    # print(f"gcp_backend_resource: {gcp_backend_resource.cloud_provider}")
                    # self._handle_exception_logging(logger, f"gcp_backend_resource: {gcp_backend_resource.cloud_provider}")
                    # logger.exception(f"gcp_backend_resource: {gcp_backend_resource.cloud_provider}")
                    # if gcp_backend_resource.cloud_provider == GCP1G_MODEL:
                    # GCP1G_MODEL:
                    clp_details = self._validate_clp(api, gcp_backend_resource, logger)
                    if clp_details.ResourceModelName == GCP1G_MODEL:
                        # account_keys = self._get_storage_keys(api, azure_backend_resource, clp_details)
                        model_prefix = ""
                        json_path = self._get_attrbiute_value_from_clp(
                            clp_details.ResourceAttributes, model_prefix, CREDENTIALS_JSON_PATH)
                        # self._handle_exception_logging(logger, f"json_pa {json_path}")
                        # logger.exception(f"json_path: {json_path}") 
                        # with open('C:\\out.txt', 'w') as f:
                        #     with redirect_stdout(f):
                        #         print('data')
                        #         print(f"JSON path: {json_path}")
                        #         print(f"gcp_backend_resource: {gcp_backend_resource.cloud_provider}")  
                        # if json_path:
                        os.environ[GOOGLE_APPLICATION_CREDENTIALS] = "C:\\Users\\CSadmin123456\\CS\\tf-gcp\\prod.json"
            except Exception as e:
                self._handle_exception_logging(logger, f"There was an issue accessing GCP. {e}") 
            bucket_name = gcp_backend_resource.bucket_name
            if bucket_name:      
                self._validate_bucket_exists(bucket_name, context)

    # def _get_storage_keys(self, api, azure_backend_resource, clp_details):
    #     azure_model_prefix = ""
    #     if clp_details.ResourceModelName == AZURE2G_MODEL:
    #         azure_model_prefix = AZURE2G_MODEL + "."
    #     self._fill_backend_sercret_vars_data(api, azure_model_prefix, clp_details.ResourceAttributes)
    #     credentials = ServicePrincipalCredentials(
    #         tenant=self._backend_secret_vars["tenant_id"],
    #         client_id=self._backend_secret_vars["client_id"],
    #         secret=self._backend_secret_vars["client_secret"]
    #     )
    #     storage_client = StorageManagementClient(
    #         credentials=credentials, subscription_id=self._backend_secret_vars["subscription_id"]
    #     )
    #     account_keys = storage_client.storage_accounts.list_keys(
    #         azure_backend_resource.resource_group, azure_backend_resource.storage_account_name
    #     )
    #     return account_keys

    def _get_attrbiute_value_from_clp(self, attributes, model_prefix, attribute_name) -> str:
        for attribute in attributes:

            if attribute.Name == f"{model_prefix}{attribute_name}":
                return attribute.Value
        return ""


    # def _fill_backend_sercret_vars_data(self, api, azure_model_prefix, clp_resource_attributes):
    #         self._backend_secret_vars = {}
    #         for attr in clp_resource_attributes:
    #             if attr.Name == azure_model_prefix + "Azure Subscription ID":
    #                 self._backend_secret_vars["subscription_id"] = attr.Value
    #             if attr.Name == azure_model_prefix + "Azure Tenant ID":
    #                 self._backend_secret_vars["tenant_id"] = attr.Value
    #             if attr.Name == azure_model_prefix + "Azure Application ID":
    #                 self._backend_secret_vars["client_id"] = attr.Value
    #             if attr.Name == azure_model_prefix + "Azure Application Key":
    #                 dec_client_secret = api.DecryptPassword(attr.Value).Value
    #                 self._backend_secret_vars["client_secret"] = dec_client_secret

    def _create_clp_gcp_session(self, json_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path


    def _validate_clp(self, api, gcp_backend_resource, logger):
        clp_resource_name = gcp_backend_resource.cloud_provider
        clp_details = api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName
        clpr_res_fam = clp_details.ResourceFamilyName
        if (clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider') or \
                clp_res_model not in GCP_MODELS:
            logger.error(f"Cloud Provider does not have the expected type: {clpr_res_fam}")
            raise ValueError(f"Cloud Provider does not have the expected type:{clpr_res_fam}")
        return clp_details

    def _handle_exception_logging(self, logger, msg):
        logger.exception(msg)
        raise ValueError(msg)

    # </editor-fold>

# if __name__ == "__main__":
#     import mock
#     from cloudshell.shell.core.driver_context import CancellationContext


#     shell_name = "Gcp Tf Backend"

#     cancellation_context = mock.create_autospec(CancellationContext)
#     context = mock.create_autospec(ResourceCommandContext)
#     context.resource = mock.MagicMock()
#     context.reservation = mock.MagicMock()
#     context.connectivity = mock.MagicMock()
#     context.reservation.reservation_id = "a29b2b18-d065-44c0-9ae6-3de9263541f7"
#     context.resource.address = "127.0.0.1"
#     context.resource.name = "myname"
#     context.resource.attributes = dict()
#     context.resource.attributes[f"{shell_name}.User"] = "admin"
#     context.resource.attributes[f"{shell_name}.Password"] = "admin"
#     context.resource.attributes[f"{shell_name}.SNMP Read Community"] = "<READ_COMMUNITY_STRING>"

#     driver = GcpTfBackendDriver()

#     # print driver.run_custom_command(context, custom_command="sh run", cancellation_context=cancellation_context)
#     # driver.initialize(context)
#     # result = driver.get_inventory(context)
#     result = driver.get_inventory(context)
#     # print(result)
#     print('done')


if __name__ == "__main__":
    import mock
    from cloudshell.shell.core.driver_context import CancellationContext


    shell_name = "Gcp Tf Backend"

    cancellation_context = mock.create_autospec(CancellationContext)
    context = mock.create_autospec(ResourceCommandContext)
    context.resource = mock.MagicMock()
    context.reservation = mock.MagicMock()
    context.connectivity = mock.MagicMock()
    context.reservation.reservation_id = "<RESERVATION_ID>"
    context.resource.address = "127.0.0.1"
    context.resource.name = "myname"
    context.resource.attributes = dict()
    context.resource.attributes["{}.User".format(shell_name)] = "<USER>"
    context.resource.attributes["{}.Password".format(shell_name)] = "<PASSWORD>"
    context.resource.attributes["{}.SNMP Read Community".format(shell_name)] = "<READ_COMMUNITY_STRING>"

    driver = GcpTfBackendDriver()

    # print driver.run_custom_command(context, custom_command="sh run", cancellation_context=cancellation_context)
    driver.initialize(context)
    result = driver.get_inventory(context)
    # result = driver.example_command(context)
    print(result)
    print('done')