from cloudshell.workflow.orchestration.sandbox import Sandbox

server_address = "192.168.33.29"
sb_id = "3af84dc6-4e23-43fc-af6a-83ca78f3a95d"

import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
dev_helpers.attach_to_cloudshell_as('admin', 'admin', 'Global', sb_id, server_address=server_address, cloudshell_api_port='8029')

sb = Sandbox()
sb.automation_api.WriteMessageToReservationOutput(sb_id, "sda")

print("")
