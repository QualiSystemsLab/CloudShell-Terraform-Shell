import json
import os
from logging import Logger

from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig

from cloudshell.iac.terraform.constants import (
    ATTRIBUTE_NAMES,
    DELETE_TFSTATE_FILE_COMMAND,
    GET_BACKEND_DATA_COMMAND,
)
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class CPBackendHandler:
    def __init__(
        self,
        resource_config: TerraformResourceConfig,
        logger: Logger,
    ):
        self._backend_resource = ""
        self._resource_config = resource_config
        self._logger = logger
        try:
            backend_resource = resource_config.remote_state_provider

            self._backend_resource = backend_resource
            self._backend_secret_vars = {}
            self.backend_exists = bool(backend_resource)
            # If the resource was referenced but not exists it would yield an Exception
            if self.backend_exists:
                self._resource_config.api.GetResourceDetails(backend_resource)

        except Exception as e:
            msg = f"Backend provider specified:[{self._backend_resource}] was not found in the inventory"
            self._logger.exception(msg)
            raise ValueError(msg)

    def generate_backend_cfg_file(
        self, app_name: str, sandbox_id: str, working_dir: str
    ):
        if self.backend_exists:
            params = [
                InputNameValue(
                    "tf_state_unique_name", f"" f"{sandbox_id}" f"_{app_name}.tf.state"
                )
            ]
            try:
                backend_data = self._resource_config.api.ExecuteCommand(
                    sandbox_id,
                    self._backend_resource,
                    "Resource",
                    GET_BACKEND_DATA_COMMAND,
                    params,
                    False,
                )
            except Exception as e:
                msg = f"Was not able to generate remote tf state file : {str(e)}"
                self._logger.exception(msg)
                raise ValueError(msg)

            backend_data_json = json.loads(backend_data.Output)

            with open(os.path.join(working_dir, "backend.tf"), "w") as backend_file:
                backend_file.write(
                    backend_data_json["backend_data"]["tf_state_file_string"]
                )
            self._backend_secret_vars = backend_data_json["backend_secret_vars"]

    def delete_backend_tf_state_file(self, app_name: str, sandbox_id: str):
        if self.backend_exists:
            params = [
                InputNameValue(
                    "tf_state_unique_name", f"{sandbox_id}_{app_name}.tf.state"
                )
            ]

            self._resource_config.api.ExecuteCommand(
                sandbox_id,
                self._backend_resource,
                "Resource",
                DELETE_TFSTATE_FILE_COMMAND,
                params,
                False,
            )

    def get_backend_secret_vars(self) -> dict:
        return self._backend_secret_vars
