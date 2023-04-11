from logging import Logger

import jsonpickle
from cloudshell.cp.core.request_actions.models import (
    ValidateAttributes,
    ValidateAttributesResponse,
)
from cloudshell.cp.terraform.actions.validation import ValidationActions
from cloudshell.cp.terraform.constants import VM_FROM_TF_GIT

# from cloudshell.cp.terraform.handlers.si_handler import SiHandler
from cloudshell.cp.terraform.models.base_deployment_app import (
    TerraformDeploymentAppAttributeNames,
)
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


def validate_attributes(
    resource_conf: TerraformResourceConfig, request: str, logger: Logger
) -> str:
    deployment_path_to_fn = {
        VM_FROM_TF_GIT: _validate_app_from_vm,
    }
    action = ValidateAttributes.from_request(request)

    fn = deployment_path_to_fn[action.deployment_path]

    result = ValidateAttributesResponse(action.actionId)
    return jsonpickle.encode(result, unpicklable=False)


def _validate_common(action: ValidateAttributes, validator: ValidationActions):
    a_names = TerraformDeploymentAppAttributeNames


def _validate_app_from_vm(action: ValidateAttributes, validator: ValidationActions):
    a_names = TerraformDeploymentAppAttributeNames
    # validator.validate_app_from_vm(action.get(a_names.TF_vm))
