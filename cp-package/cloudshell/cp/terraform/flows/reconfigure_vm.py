from __future__ import annotations

from logging import Logger

# from cloudshell.cp.terraform.models.deployed_app import VMFromTerraformGit
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


def reconfigure_vm(
    resource_conf: TerraformResourceConfig,
    # deployed_app: VMFromTerraformGit,
    cpu: str | None,
    ram: str | None,
    hdd: str | None,
    logger: Logger,
):
    logger.info("Reconfiguring VM")
