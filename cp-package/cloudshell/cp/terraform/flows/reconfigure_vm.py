from __future__ import annotations

from logging import Logger

from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.cp.terraform.terraform_cp_shell import TerraformCPShell


def reconfigure_vm(
    deployed_app: BaseTFDeployedApp,
    resource_conf: TerraformResourceConfig,
    reservation_id: str,
    logger: Logger,
) -> str:
    logger.info("Reconfiguring VM")

    tf_exec = TerraformCPShell(
        resource_config=resource_conf,
        logger=logger,
        sandbox_id=reservation_id,
    )
    output = tf_exec.update_terraform(deployed_app, deployed_app.name)

    logger.info("Finished delete instance command")
    if output.address:
        deployed_app.update_private_ip(deployed_app.name, output.address)
    return output.address
