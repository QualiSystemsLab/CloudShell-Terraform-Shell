import json
import os

from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext
#from data_model import *  # run 'shellfoundry generate' to generate data model classes
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from data_model import AzureTfBackend


class AzureTfBackendDriver (ResourceDriverInterface):

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
        resource = AzureTfBackend.create_from_context(context)
        resource.vendor = 'specify the shell vendor'
        resource.model = 'specify the shell model'

        port1 = ResourcePort('Port 1')
        port1.ipv4_address = '192.168.10.7'
        resource.add_sub_resource('1', port1)

        return resource.create_autoload_details()
        '''
        return AutoLoadDetails([], [])

    # </editor-fold>

    # <editor-fold desc="Orchestration Save and Restore Standard">
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

    def return_backend_data(self, context, tf_state_unique_name):
        with LoggingSessionContext(context) as logger:
            azure_backend_resource = AzureTfBackend.create_from_context(context)
            tf_state_file_string = '''terraform {
backend "azurerm" {
    storage_account_name = AAA
    container_name       = BBB
    key                  = CCC
    }
}'''
            azure_backend_resource.storage_account_name = "BLA"
            tf_state_file_string1 = tf_state_file_string.replace("AAA", azure_backend_resource.storage_account_name)
            azure_backend_resource.container_name = "BLA"
            tf_state_file_string2 = tf_state_file_string1.replace("BBB", azure_backend_resource.container_name)
            tf_state_file_string3 = tf_state_file_string2.replace("CCC", tf_state_unique_name)

            backend_data = {"tf_state_file_string": tf_state_file_string3}
            '''
            api = CloudShellSessionContext(context).get_api()
            dec_access_key = api.DecryptPassword(azure_backend_resource.access_key).Value
            backend_env_vars = {
                "access_key": dec_access_key
            }
            api.WriteMessageToReservationOutput(context.reservation.reservation_id, os.getcwd())
            '''
            f = open("test.tf", "a")
            f.write(tf_state_file_string3)
            f.close()
            backend_env_vars = "BLA"
            response = json.dumps({"backend_data": backend_data , "backend_env_vars": backend_env_vars})
            return response


if __name__ == "__main__":
    import mock
    from cloudshell.shell.core.driver_context import CancellationContext

    shell_name = "AzureTfBackend"

    cancellation_context = mock.create_autospec(CancellationContext)
    context = mock.create_autospec(ResourceCommandContext)
    context.resource = mock.MagicMock()
    context.reservation = mock.MagicMock()
    context.connectivity = mock.MagicMock()
    # context.reservation.reservation_id = "<RESERVATION_ID>"
    # context.resource.address = "<RESOURCE_ADDRESS>"
    context.resource.name = "RESOURCE_NAME"
    context.resource.resource_name = "RESOURCE_NAME"
    context.reservation.reservation_id = "d9bfd604-64e8-4923-9e93-bef05db397d2"
    context.resource.storage_account_name = "1"
    context.resource.container_name = "2"
    context.resource.access_key = "3"



    context.resource.attributes = dict()
    context.resource.attributes["{}.Storage Account Name".format(shell_name)] = "<Storage Account Name>"
    context.resource.attributes["{}.Container Name".format(shell_name)] = "<Container Name>"
    context.resource.attributes["{}.Access Key".format(shell_name)] = "3M3u7nkDzxWb0aJ/IZYeWw=="

    driver = AzureTfBackendDriver()
    # print driver.run_custom_command(context, custom_command="sh run", cancellation_context=cancellation_context)
    driver.initialize(context)
    result = driver.return_backend_data(context, "a")

    print("done")
