import json
import os
from logging import Logger

from cloudshell.api.cloudshell_api import CloudShellAPISession, InputNameValue

# from tests.constants import GET_BACKEND_DATA_COMMAND
from cloudshell.iac.terraform.constants import GET_BACKEND_DATA_COMMAND, DELETE_TFSTATE_FILE_COMMAND, ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class BackendHandler(object):
    def __init__(
        self,
        shell_helper: ShellHelperObject,
        working_dir: str,
        uuid: str
    ):
        self._backend_resource = ""
        try:
            backend_resource = shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.REMOTE_STATE_PROVIDER)
            if shell_helper.api.GetResourceDetails(backend_resource):
                self._shell_helper = shell_helper
                self._working_dir = working_dir
                self._reservation_id = shell_helper.sandbox_id
                self._backend_resource = backend_resource
                self._uuid = uuid
                self._backend_secret_vars = {}
                self.backend_exists = bool(backend_resource)

        except Exception as e:
            msg = f"Backend provider specified:[{self._backend_resource}] was not found in the inventory"
            shell_helper.logger.exception(msg)
            raise ValueError(msg)

    def generate_backend_cfg_file(self):
        if self.backend_exists:
            params = [InputNameValue("tf_state_unique_name", f"{self._reservation_id}_{self._uuid}.tf.state")]

            backend_data = self._shell_helper.api.ExecuteCommand(
                self._reservation_id,
                self._backend_resource,
                "Resource",
                GET_BACKEND_DATA_COMMAND,
                params,
                False
            )
            backend_data_json = json.loads(backend_data.Output)

            with open(os.path.join(self._working_dir, "backend.tf"), "w") as backend_file:
                backend_file.write(backend_data_json['backend_data']['tf_state_file_string'])
            self._backend_secret_vars = backend_data_json["backend_secret_vars"]

    def delete_backend_tf_state_file(self):
        if self.backend_exists:
            params = [InputNameValue("tf_state_unique_name", f"{self._reservation_id}_{self._uuid}.tf.state")]

            self._shell_helper.api.ExecuteCommand(
                self._reservation_id,
                self._backend_resource,
                "Resource",
                DELETE_TFSTATE_FILE_COMMAND,
                params,
                False
            )

    def get_backend_secret_vars(self) -> dict:
        return self._backend_secret_vars
