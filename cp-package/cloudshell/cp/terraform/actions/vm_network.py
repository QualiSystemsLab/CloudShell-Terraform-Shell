from __future__ import annotations

import re
import time
from contextlib import nullcontext
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

# from cloudshell.cp.terraform.exceptions import VMIPNotFoundException
# from cloudshell.cp.terraform.handlers.network_handler import NetworkHandler
# from cloudshell.cp.terraform.handlers.vm_handler import VmHandler

if TYPE_CHECKING:
    from logging import Logger

    from cloudshell.cp.core.cancellation_manager import CancellationContextManager

    from cloudshell.cp.terraform.resource_config import TFResourceConfig


class VMNetworkActions:
    QUALI_NETWORK_PREFIX = "QS_"
    DEFAULT_IP_REGEX = ".*"
    DEFAULT_IP_DELAY = 5

    def __init__(
        self,
        resource_conf: TFResourceConfig,
        logger: Logger,
        cancellation_manager: CancellationContextManager | nullcontext = nullcontext(),
    ):
        self._resource_conf = resource_conf
        self._logger = logger
        self._cancellation_manager = cancellation_manager

    def is_quali_network(self, network_name: str) -> bool:
        return network_name.startswith(self.QUALI_NETWORK_PREFIX)

    def _find_vm_ip(
        self,
        # vm: VmHandler,
        skip_networks: list[NetworkHandler],
        is_ip_pass_regex: callable[[str | None], bool],
    ) -> str | None:
        self._logger.info(f"Searching for the IPv4 address of the {vm}")
        ip = vm.primary_ipv4
        if not ip:
            self._logger.debug(f"{vm} doesn't have a primary IPv4 address")
            for vnic in vm.vnics:
                if vnic.network not in skip_networks and is_ip_pass_regex(vnic.ipv4):
                    self._logger.debug(f"Found IP {vnic.ipv4} on {vnic}")
                    ip = vnic.ipv4
                    break
        return ip

    def get_vm_ip(
        self,
        vm: VmHandler,
        ip_regex: str | None = None,
        timeout: int = 0,
        skip_networks: list[NetworkHandler] | None = None,
    ) -> str:
        self._logger.info(f"Getting IP address for the VM {vm.name} from the TF")
        timeout_time = datetime.now() + timedelta(seconds=timeout)
        is_ip_pass_regex = get_ip_regex_match_func(ip_regex)
        skip_networks = skip_networks or []

        while True:
            with self._cancellation_manager:
                ip = self._find_vm_ip(vm, skip_networks, is_ip_pass_regex)
            if ip:
                break
            if datetime.now() > timeout_time:
                raise VMIPNotFoundException("Unable to get VM IP")
            time.sleep(self.DEFAULT_IP_DELAY)
        return ip


def get_ip_regex_match_func(ip_regex=None) -> callable[[str | None], bool]:
    """Get Regex Match function for the VM IP address."""
    pattern = re.compile(ip_regex) if ip_regex is not None else None

    def is_ip_pass_regex(ip: str | None) -> bool:
        if not ip:
            result = False
        elif not pattern:
            result = True
        else:
            result = bool(pattern.match(ip))
        return result

    return is_ip_pass_regex
