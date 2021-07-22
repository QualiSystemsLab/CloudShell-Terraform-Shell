import json

from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadDetails

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from constants import AZURE2G_MODEL, AZURE_MODELS
from data_model import AzureTfBackend

from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential


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

                if azure_backend_resource.access_key:
                    if azure_backend_resource.cloud_provider:
                        self._handle_value_error_exception(logger, "Only one method of authentication should be filled")
                    credentials = api.DecryptPassword(azure_backend_resource.access_key).Value

                else:
                    if azure_backend_resource.cloud_provider:
                        clp_details = self._validate_clp(api, azure_backend_resource, logger)

                        azure_model_prefix = ""
                        if clp_details.ResourceModelName == AZURE2G_MODEL:
                            azure_model_prefix = AZURE2G_MODEL + "."

                        self._fill_backend_sercret_vars_data(api, azure_model_prefix, clp_details.ResourceAttributes)
                        credentials = ClientSecretCredential(
                            self._backend_secret_vars["tenant_id"],
                            self._backend_secret_vars["client_id"],
                            self._backend_secret_vars["client_secret"]
                        )

                    else:
                        self._handle_value_error_exception(logger, "Inputs for Cloud Backend Access missing")

            except Exception as e:
                self._handle_value_error_exception(logger, "Inputs for Cloud Backend Access missing or incorrect")

            try:
                blob_svc_client = BlobServiceClient(
                    account_url="https://{}.blob.core.windows.net/".format(azure_backend_resource.storage_account_name),
                    credential=credentials
                )
                blob_svc_container_client = blob_svc_client.get_container_client(azure_backend_resource.container_name)
                blob_svc_container_client.get_container_properties()
            except ResourceNotFoundError:
                self._handle_value_error_exception(
                    logger, "Was not able to locate container referenced {}".format(azure_backend_resource.container_name)
                )
            except ClientAuthenticationError as e:
                self._handle_value_error_exception(
                    logger, "Was not able to Authenticate in order to validate azure backend storage"
                )
        return AutoLoadDetails([], [])

    def _handle_value_error_exception(self, logger, msg):
        logger.exception(msg)
        raise ValueError(msg)

    # </editor-fold>

    def get_backend_data(self, context, tf_state_unique_name):
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
                        logger.exception("Inputs for Cloud Backend Access missing")
                        raise ValueError("Inputs for Cloud Backend Access missing")

            except Exception as e:
                self._handle_value_error_exception(logger, "Inputs for Cloud Backend Access missing or incorrect")

            logger.info("Returning backend data for creating provider file :\n{}".format(backend_data))
            response = json.dumps({"backend_data": backend_data, "backend_secret_vars": self._backend_secret_vars})
            return response

    def _generate_state_file_string(self, azure_backend_resource, tf_state_unique_name):
        tf_state_file_string = 'terraform {{\n\
\tbackend "azurerm" {{\n\
\t\tstorage_account_name = "{0}"\n\
\t\tcontainer_name       = "{1}"\n\
\t\tkey                  = "{2}"\n\
\t}}\n\
}}'.format(azure_backend_resource.storage_account_name, azure_backend_resource.container_name, tf_state_unique_name)
        return tf_state_file_string

    def _validate_clp(self, api, azure_backend_resource, logger):
        clp_resource_name = azure_backend_resource.attributes['{0}.{1}'.
            format(azure_backend_resource.cloudshell_model_name, "Cloud Provider")]
        clp_details = api.GetResourceDetails(clp_resource_name)
        clp_res_model = clp_details.ResourceModelName
        clpr_res_fam = clp_details.ResourceFamilyName
        if (clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider') or \
                clp_res_model not in AZURE_MODELS:
            logger.error("Cloud Provider does not have the expected type: {}".format(clpr_res_fam))
            raise ValueError("Cloud Provider does not have the expected type: {}".format(clpr_res_fam))
        return clp_details

    def _fill_backend_sercret_vars_data(self, api, azure_model_prefix, clp_resource_attributes):
        for attr in clp_resource_attributes:
            self._backend_secret_vars = {}
            if attr.Name == azure_model_prefix + "Azure Subscription ID":
                self._backend_secret_vars["subscription_id"] = attr.Value
            if attr.Name == azure_model_prefix + "Azure Tenant ID":
                self._backend_secret_vars["tenant_id"] = attr.Value
            if attr.Name == azure_model_prefix + "Azure Application ID":
                self._backend_secret_vars["client_id"] = attr.Value
            if attr.Name == azure_model_prefix + "Azure Application Key":
                dec_client_secret = api.DecryptPassword(attr.Value).Value
                self._backend_secret_vars["client_secret"] = dec_client_secret
