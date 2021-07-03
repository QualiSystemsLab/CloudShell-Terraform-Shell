from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.iac.terraform.terraform_shell import TerraformShell
from data_model import *  # run 'shellfoundry generate' to generate data model classes


class TerraformService2GDriver (ResourceDriverInterface):

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

    def execute_terraform(self, context: ResourceCommandContext):
        with LoggingSessionContext(context) as logger:
            tf_service = TerraformService2G.create_from_context(context)
            tf_shell = TerraformShell(context, tf_service, logger)
            tf_shell.execute_terraform()

    def destroy_terraform(self, context: ResourceCommandContext):
        with LoggingSessionContext(context) as logger:
            tf_service = TerraformService2G.create_from_context(context)
            tf_shell = TerraformShell(context, tf_service, logger)
            tf_shell.destroy_terraform()
