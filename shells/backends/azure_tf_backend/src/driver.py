import json

from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadDetails
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from constants import AZURE2G_MODEL, AZURE_MODELS
from data_model import AzureTfBackend

from azure.storage.blob import BlobServiceClient

from msrestazure.azure_active_directory import ServicePrincipalCredentials
from azure.mgmt.storage import StorageManagementClient


class AzureTfBackendDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self._backend_secret_vars = {}
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

        with LoggingSessionContext(context) as logger:
            azure_backend_resource = AzureTfBackend.create_from_context(context)
            try:
                api = CloudShellSessionContext(context).get_api()

                if api.DecryptPassword(azure_backend_resource.access_key).Value:
                    if azure_backend_resource.cloud_provider:
                        self._handle_exception_logging(logger, "Only one method of authentication should be filled")
                    credential = api.DecryptPassword(azure_backend_resource.access_key).Value
                else:
                    if azure_backend_resource.cloud_provider:
                        clp_details = self._validate_clp(api, azure_backend_resource, logger)

                        account_keys = self._get_storage_keys(api, azure_backend_resource, clp_details)
                        if not account_keys.keys:
                            self._handle_exception_logging(logger, f"Unable to find access key for the storage account")
                        credential = account_keys.keys[0].value
                    else:
                        self._handle_exception_logging(logger, "Inputs for Cloud Backend Access missing")
            except Exception as e:
                self._handle_exception_logging(logger, "Inputs for Cloud Backend Access missing or incorrect")

            try:
                self._validate_container_exists(azure_backend_resource, credential)
            except ResourceNotFoundError:
                self._handle_exception_logging(
                    logger, f"Was not able to locate container referenced {azure_backend_resource.container_name}"
                )
            except ClientAuthenticationError as e:
                self._handle_exception_logging(
                    logger, "Was not able to Authenticate in order to validate azure backend storage"
                )
        return AutoLoadDetails([], [])

    def _validate_container_exists(self, azure_backend_resource, credential):
        blob_svc_client = BlobServiceClient(
            account_url=f"https://{azure_backend_resource.storage_account_name}.blob.core.windows.net/",
            credential=credential
        )
        blob_svc_container_client = blob_svc_client.get_container_client(azure_backend_resource.container_name)
        # The following command will yield an exception in case container does not exist
        blob_svc_container_client.get_container_properties()

    def _get_storage_keys(self, api, azure_backend_resource, clp_details):
        azure_model_prefix = ""
        if clp_details.ResourceModelName == AZURE2G_MODEL:
            azure_model_prefix = AZURE2G_MODEL + "."
        self._fill_backend_sercret_vars_data(api, azure_model_prefix, clp_details.ResourceAttributes)
        credentials = ServicePrincipalCredentials(
            tenant=self._backend_secret_vars["tenant_id"],
            client_id=self._backend_secret_vars["client_id"],
            secret=self._backend_secret_vars["client_secret"]
        )
        storage_client = StorageManagementClient(
            credentials=credentials, subscription_id=self._backend_secret_vars["subscription_id"]
        )
        account_keys = storage_client.storage_accounts.list_keys(
            azure_backend_resource.resource_group, azure_backend_resource.storage_account_name
        )
        return account_keys

    def _handle_exception_logging(self, logger, msg):
        logger.exception(msg)
        raise ValueError(msg)

    def get_backend_data(self, context, tf_state_unique_name: str) -> str:
        with LoggingSessionContext(context) as logger:
            azure_backend_resource = AzureTfBackend.create_from_context(context)
            tf_state_file_string = self._generate_state_file_string(azure_backend_resource, tf_state_unique_name)

            backend_data = {"tf_state_file_string": tf_state_file_string}
            try:
                api = CloudShellSessionContext(context).get_api()

                if azure_backend_resource.access_key:
                    dec_access_key = api.DecryptPassword(azure_backend_resource.access_key).Value
                    self._backend_secret_vars = {"access_key": dec_access_key}
                else:
                    if azure_backend_resource.cloud_provider:
                        clp_details = self._validate_clp(api, azure_backend_resource, logger)

                        azure_model_prefix = ""
                        if clp_details.ResourceModelName == AZURE2G_MODEL:
                            azure_model_prefix = AZURE2G_MODEL + "."
                        self._fill_backend_sercret_vars_data(api, azure_model_prefix, clp_details.ResourceAttributes)
                    else:
                        self._handle_exception_logging(logger, "Inputs for Cloud Backend Access missing")

            except Exception as e:
                self._handle_exception_logging(logger, "Inputs for Cloud Backend Access missing or incorrect")

            logger.info(f"Returning backend data for creating provider file :\n{backend_data}")
            response = json.dumps({"backend_data": backend_data, "backend_secret_vars": self._backend_secret_vars})
            return response

    def _generate_state_file_string(self, azure_backend_resource, tf_state_unique_name):
        tf_state_file_string = f'terraform {{\n\
\tbackend "azurerm" {{\n\
\t\tstorage_account_name = "{azure_backend_resource.storage_account_name}"\n\
\t\tcontainer_name       = "{azure_backend_resource.container_name}"\n\
\t\tkey                  = "{tf_state_unique_name}"\n\
\t}}\n\
}}'
        return tf_state_file_string

    def _validate_clp(self, api, azure_backend_resource, logger):
        clp_resource_name = azure_backend_resource.cloud_provider
        clp_details = api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName
        clpr_res_fam = clp_details.ResourceFamilyName
        if (clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider') or \
                clp_res_model not in AZURE_MODELS:
            logger.error(f"Cloud Provider does not have the expected type: {clpr_res_fam}")
            raise ValueError(f"Cloud Provider does not have the expected type:{clpr_res_fam}")
        return clp_details

    def _fill_backend_sercret_vars_data(self, api, azure_model_prefix, clp_resource_attributes):
        self._backend_secret_vars = {}
        for attr in clp_resource_attributes:
            if attr.Name == azure_model_prefix + "Azure Subscription ID":
                self._backend_secret_vars["subscription_id"] = attr.Value
            if attr.Name == azure_model_prefix + "Azure Tenant ID":
                self._backend_secret_vars["tenant_id"] = attr.Value
            if attr.Name == azure_model_prefix + "Azure Application ID":
                self._backend_secret_vars["client_id"] = attr.Value
            if attr.Name == azure_model_prefix + "Azure Application Key":
                dec_client_secret = api.DecryptPassword(attr.Value).Value
                self._backend_secret_vars["client_secret"] = dec_client_secret
