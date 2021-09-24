import os
import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from cloudshell.api.cloudshell_api import AttributeNameValue
from cloudshell.workflow.orchestration.sandbox import Sandbox
from tests.integration_tests.constants import SHELL_NAME, UUID_ATTRIBUTE

from dotenv import load_dotenv

load_dotenv()

server_address = os.environ.get("CS_SERVER")
sb_id = os.environ.get("RESERVATION_ID")
cs_user = os.environ.get("CS_USERNAME")
cs_pass = os.environ.get("CS_PASSWORD")
cs_domain = os.environ.get("RESERVATION_DOMAIN")


dev_helpers.attach_to_cloudshell_as(cs_user, cs_pass, cs_domain, sb_id, server_address=server_address, cloudshell_api_port='8029')


def print_uuids(sb: Sandbox):
    services = sb.automation_api.GetReservationDetails(sb_id, disableCache=True).ReservationDescription.Services
    for service in services:
        for attribute in service.Attributes:
            if attribute.Name == f"{SHELL_NAME}.UUID":
                service_data = ""
                data = sb.automation_api.GetSandboxData(sb_id)
                for sbdkv in data.SandboxDataKeyValues:
                    if sbdkv.Key == attribute.Value:
                        service_data = sbdkv.Value
                print(f"{service.Alias}.UUID={attribute.Value} \n data={service_data}\n\n")
                continue


def wipe_uuids(sb: Sandbox):
    services = sb.automation_api.GetReservationDetails(sb_id, disableCache=True).ReservationDescription.Services
    attr_req = [AttributeNameValue(UUID_ATTRIBUTE, "")]

    for service in services:
        sb.automation_api.SetServiceAttributesValues(sb_id, service.Alias, attr_req)


sb = Sandbox()
# print_uuids(sb)
# wipe_uuids(sb)
# data = sb.automation_api.GetSandboxData(sb_id)
print("")
