from logging import Logger

import jsonpickle

from cloudshell.cp.terraform.flows.get_attribute_hints.deployment_type_handlers import (
    get_handler,
)

from cloudshell.cp.terraform.models.DeployDataHolder import DeployDataHolder
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


def get_hints(
    resource_conf: TerraformResourceConfig,
    request: str,
    logger: Logger,
) -> str:
    # todo replace with a model
    request = DeployDataHolder(jsonpickle.decode(request))

    handler = get_handler(request, dc)
    response = handler.prepare_hints()
    return jsonpickle.encode(response, unpicklable=False)
