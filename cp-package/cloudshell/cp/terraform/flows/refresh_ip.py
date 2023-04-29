from __future__ import annotations

from contextlib import suppress
from logging import Logger

from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.cp.terraform.terraform_cp_shell import TerraformCPShell


def refresh_ip(
    deployed_app: BaseTFDeployedApp,
    resource_conf: TerraformResourceConfig,
    reservation_id: str,
    logger: Logger,
    ) -> str:
    logger.info("Starting delete instance command...")
    with suppress(Exception):
        if any(x for x in deployed_app.terraform_app_outputs_map.values() if
                x.casefold() == "address"):
            return ""
        tf_exec = TerraformCPShell(
            resource_config=resource_conf,
            logger=logger,
            sandbox_id=reservation_id,
        )
        output = tf_exec.refresh_terraform(deployed_app)

        logger.info("Finished delete instance command")
        if output.address:
            deployed_app.update_private_ip(deployed_app.name, output.address)
        return output.address
