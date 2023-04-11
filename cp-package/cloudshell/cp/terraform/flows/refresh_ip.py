from __future__ import annotations

from logging import Logger

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.terraform.actions.vm_network import VMNetworkActions
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig

# def refresh_ip(
#     deployed_app: BaseTFDeployedApp ,
#     resource_conf: TerraformResourceConfig,
#     cancellation_manager: CancellationContextManager,
#     _logger: Logger,
# ) -> str:
# vm = dc.get_vm_by_uuid(deployed_app.vmdetails.uid)
# if vm.power_state is not vm.power_state.ON:
#     # raise VmIsNotPowered(vm)
#     pass
# actions = VMNetworkActions(resource_conf, _logger, cancellation_manager)
# if isinstance(deployed_app, BaseTFDeployedApp):
# #     ip = actions.get_vm_ip(vm)
# # else:
#     default_net = dc.get_network(resource_conf.holding_network)
#     ip = actions.get_vm_ip(
#         vm,
#         ip_regex=deployed_app.ip_regex,
#         timeout=deployed_app.refresh_ip_timeout,
#         skip_networks=[default_net],
#     )
# if ip != deployed_app.private_ip:
#     deployed_app.update_private_ip(deployed_app.name, ip)
# return ip
