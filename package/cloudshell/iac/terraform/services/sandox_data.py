import json

from cloudshell.api.cloudshell_api import SandboxDataKeyValue, GetSandboxDataInfo

from cloudshell.iac.terraform.constants import EXECUTE_STATUS, DESTROY_STATUS, NONE, TF_WORKING_DIR, ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class SandboxDataHandler(object):
    def __init__(self, driver_helper_obj: ShellHelperObject, tf_working_dir: str = None):
        self._driver_helper_obj = driver_helper_obj
        self._uuid = self._driver_helper_obj.attr_handler.get_attribute(ATTRIBUTE_NAMES.UUID)
        if not self._ged_uuid_data_as_str():
            self._create_tf_exec_state_data_entry(self._uuid)
        self._tf_working_dir = self._get_tf_working_dir(tf_working_dir)

    def get_tf_uuid(self) -> str:
        return self._uuid

    def _get_tf_working_dir(self, tf_working_dir: str) -> str:
        # if tf_working_dir was not provided we need to get the information from the SB DATA
        if not tf_working_dir:
            return self.get_tf_working_dir()
        # if tf_working_dir was provided we need to set the information in SB DATA and also return it
        else:
            self.set_tf_working_dir(tf_working_dir)
            return tf_working_dir

    # This creates the uuid:state(statuses...) entry
    def _create_tf_exec_state_data_entry(self, uuid: str) -> None:
        first_entry = self._generate_first_uuid_state_entry()
        new_sdkv = SandboxDataKeyValue(uuid, first_entry)
        self._add_entry_to_sandbox_data(new_sdkv)

    def _add_entry_to_sandbox_data(self, sdkv_to_add: SandboxDataKeyValue) -> None:
        self._driver_helper_obj.api.SetSandboxData(self._driver_helper_obj.sandbox_id, [sdkv_to_add])

    def _generate_first_uuid_state_entry(self) -> str:
        first_tf_exec_status_data_entry = {
            EXECUTE_STATUS: NONE,
            DESTROY_STATUS: NONE,
            TF_WORKING_DIR: NONE
        }
        return json.dumps(first_tf_exec_status_data_entry)

    def _get_sb_data_val_by_key(self, sandbox_data: GetSandboxDataInfo, key: str):
        value = [attr.Value for attr in sandbox_data.SandboxDataKeyValues if attr.Key == key]
        if value.__len__() >= 1:
            return value[0]

    def set_status(self, status_type: str, status: str) -> None:
        self._set_value_for_key(status_type, status)

    def get_status(self, status_type: str) -> str:
        return self._get_value_for_key(status_type)

    def set_tf_working_dir(self, tf_working_dir: str) -> None:
        self._set_value_for_key(TF_WORKING_DIR, tf_working_dir)

    def get_tf_working_dir(self) -> str:
        return self._get_value_for_key(TF_WORKING_DIR)

    def _set_value_for_key(self, key: str, new_value: str = ""):
        uuid_sdkv_value = self._check_for_uuid_data()
        uuid_sdkv_value[key] = new_value
        updated_sdkv = SandboxDataKeyValue(self._uuid, json.dumps(uuid_sdkv_value))
        self._driver_helper_obj.api.SetSandboxData(self._driver_helper_obj.sandbox_id, [updated_sdkv])

    def _get_value_for_key(self, key: str) -> str:
        uuid_sdkv_value = self._check_for_uuid_data()
        return uuid_sdkv_value[key]

    def _check_for_uuid_data(self) -> dict:
        uuid_sdkv = self._ged_uuid_data_as_str()
        if not uuid_sdkv:
            raise Exception("Missing uuid data in sandbox data")
        return json.loads(uuid_sdkv)

    def _ged_uuid_data_as_str(self) -> str:
        current_data = self._driver_helper_obj.api.GetSandboxData(self._driver_helper_obj.sandbox_id)
        uuid_sdkv = self._get_sb_data_val_by_key(current_data, self._uuid)
        return uuid_sdkv
