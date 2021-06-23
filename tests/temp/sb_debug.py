from cloudshell.logging.qs_logger import get_qs_logger
import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.workflow.orchestration.sandbox import Sandbox
import mock,os

CS_SERVER = "192.168.0.138"
CS_SERVER2 = "192.168.33.37"
CS_USERNAME = "admin"
CS_PASSWORD = "admin"
RESERVATION_DOMAIN = "Global"

RESERVATION_ID = "d9bfd604-64e8-4923-9e93-bef05db397d2"

context = mock.create_autospec(ResourceCommandContext)
context.connectivity = mock.MagicMock()
context.connectivity.server_address = CS_SERVER
context.resource = mock.MagicMock()
context.resource.attributes = dict()
context.resource.name = "service_test"
context.resource.resource_name = "TEST123"
context.reservation = mock.MagicMock()
context.reservation.reservation_id = RESERVATION_ID
context.reservation.domain = RESERVATION_DOMAIN

dev_helpers.attach_to_cloudshell_as(CS_USERNAME,
                                    CS_PASSWORD,
                                    RESERVATION_DOMAIN,
                                    RESERVATION_ID,
                                    CS_SERVER,
                                    cloudshell_api_port='8029')
sandbox = Sandbox()
api = sandbox.automation_api

tf_service = sandbox.components.services['ooo']
cmds = api.GetServiceCommands(tf_service.ServiceName)
# api.ExecuteServiceCommand(RESERVATION_ID,tf_service.Alias,'execute_terraform')


qs_logger = get_qs_logger(
            log_group="BLA", log_category="QS", log_file_prefix="TESTBLA"
        )
qs_logger.info("BLA2")


with LoggingSessionContext(context) as logger:
    filename = logger.handlers[0].baseFilename
    path_to_log = os.sep.join(filename.split(os.sep)[:-1])
    logger.handlers[0].baseFilename = os.path.join(path_to_log,"testlog.txt")
    # logger = get_qs_logger(log_file_prefix="TF-plan")
    logger.error("BLA2")

print("")
