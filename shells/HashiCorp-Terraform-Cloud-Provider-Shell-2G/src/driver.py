from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.shell.core.driver_context import AutoLoadDetails, \
    ResourceCommandContext, CancellationContext

from cloudshell.cp.terraform.flows.deploy_vm.base_flow import TFDeployVMFlow
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit, \
    VMFromTerraformGitRequestActions
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


class HashiCorpTerraformCloudProviderShell2GDriver(ResourceDriverInterface):

    def __init__(self):
        """Init function. """
        pass

    def initialize(self, context):
        """Called every time a new instance of the driver is created.

        This method can be left unimplemented but this is a good place to
        load and cache the driver configuration, initiate sessions etc.
        Whatever you choose, do not remove it.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def get_inventory(self, context):
        """Called when the cloud provider resource is created in the inventory.

        Method validates the values of the cloud provider attributes, entered by
        the user as part of the cloud provider resource creation. In addition,
        this would be the place to assign values programmatically to optional
        attributes that were not given a value by the user. If one of the
        validations failed, the method should raise an exception
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource
        you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Autoload command...")
            api = CloudShellSessionContext(context).get_api()

        return AutoLoadDetails([], [])

    def Deploy(
            self,
            context: ResourceCommandContext,
            request: str,
            cancellation_context: CancellationContext,
    ) -> str:
        """Called when reserving a sandbox during setup.

        Method creates the compute resource in the cloud provider - VM instance or
        container. If App deployment fails, return a "success false" action result.
        :param request: A JSON string with the list of requested deployment actions
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Deploy command")
            logger.debug(f"Request: {request}")
            api = CloudShellSessionContext(context).get_api()
            resource_config = TerraformResourceConfig.from_context(context, api=api)

            cancellation_manager = CancellationContextManager(cancellation_context)
            reservation_info = ReservationInfo.from_resource_context(context)

            request_actions = VMFromTerraformGitRequestActions.from_request(request, api)
            deploy_flow = TFDeployVMFlow(
                resource_config=resource_config,
                reservation_info=reservation_info,
                cs_api=api,
                cancellation_manager=cancellation_manager,
                logger=logger,
            )
            return deploy_flow.deploy(request_actions=request_actions)

    def PowerOnHidden(self, context, ports):
        self.PowerOn(context, ports)
        # set live status on deployed app if power on passed
        api = CloudShellSessionContext(context).get_api()
        resource = context.remote_endpoints[0]
        api.SetResourceLiveStatus(resource.fullname, "Online", "Active")

    def PowerOn(self, context, ports):
        """Called when reserving a sandbox during setup.

        Call for each app in the sandbox can also be run manually by
        the sandbox end-user from the deployed App's commands pane.
        Method spins up the VM If the operation fails, method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power On command...")
            api = CloudShellSessionContext(context).get_api()

    def PowerOff(self, context, ports):
        """Called during sandbox's teardown.

        Can also be run manually by the sandbox end-user from the deployed
        App's commands pane. Method shuts down (or powers off) the VM instance.
        If the operation fails, method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power Off command...")
            api = CloudShellSessionContext(context).get_api()

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        """Called when reserving a sandbox during setup.

        Call for each app in the sandbox can also be run manually by the
        sandbox end-user from the deployed App's commands pane.
        Method retrieves the VM's updated IP address from the cloud provider
        and sets it on the deployed App resource. Both private and public IPs
        are retrieved, as appropriate. If the operation fails, method should
        raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        :param CancellationContext cancellation_context:
        :return:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Refresh IP command...")
            api = CloudShellSessionContext(context).get_api()

    def GetVmDetails(self, context, requests, cancellation_context):
        """Called when reserving a sandbox during setup.

        Call for each app in the sandbox can also be run manually by the sandbox
        end-user from the deployed App's VM Details pane. Method queries
        cloud provider for instance operating system, specifications and networking
        information and returns that as a json serialized driver response
        containing a list of VmDetailsData. If the operation fails,
        method should raise an exception.
        :param ResourceCommandContext context:
        :param str requests:
        :param CancellationContext cancellation_context:
        :return:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get VM Details command...")
            logger.debug(f"Requests: {requests}")
            api = CloudShellSessionContext(context).get_api()

    def DeleteInstance(self, context, ports):
        """Called when removing a deployed App from the sandbox.

        Method deletes the VM from the cloud provider. If the operation fails,
        method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Delete Instance command...")
            api = CloudShellSessionContext(context).get_api()

    def cleanup(self):
        """Destroy the driver session.

        This function is called every time a driver instance is destroyed.
        This is a good place to close any open sessions, finish writing
        to log files, etc.
        """
        pass
