from __future__ import annotations

from contextlib import suppress
from logging import Logger
from threading import Lock

from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.cp.terraform.terraform_cp_shell import TerraformCPShell

from cloudshell.iac.terraform.tagging.tags import TagsManager

folder_delete_lock = Lock()


def delete_instance(
    deployed_app: BaseTFDeployedApp,
    resource_conf: TerraformResourceConfig,
    reservation_info: ReservationInfo,
    logger: Logger,
):
    """Delete a VM instance from a Terraform deployment.

    :param BaseTFDeployedApp deployed_app: The deployed app to delete
    :param TerraformResourceConfig resource_conf: The resource config
    :param ReservationInfo reservation_info: The reservation info
    :param Logger logger: The logger
    """
    logger.info("Starting delete instance command...")
    # with suppress(Exception):
    tf_exec = TerraformCPShell(
        resource_config=resource_conf,
        logger=logger,
        sandbox_id=reservation_info.reservation_id,
    )
    tf_exec.destroy_terraform(deployed_app)

    logger.info("Finished delete instance command")
