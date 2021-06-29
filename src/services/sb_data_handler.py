import json
import uuid

from cloudshell.api.cloudshell_api import SandboxDataKeyValue, AttributeNameValue, GetSandboxDataInfo

from constants import EXECUTE_STATUS, DESTROY_STATUS, NONE
from driver_helper_obj import DriverHelperObject


class SbDataHandler(object):
    def __init__(self, driver_helper_obj: DriverHelperObject):
        self._driver_helper_obj = driver_helper_obj
        self._uuid = self._get_tf_uuid()

    def _get_tf_uuid(self) -> str:
        # if uuid exists as attribute just return it
        if self._driver_helper_obj.tf_service.uuid:
            return self._driver_helper_obj.tf_service.uuid
        else:
            # Create new uuid and set it on the the attribute
            new_uuid = uuid.uuid4().hex
            attr_name = f"{self._driver_helper_obj.tf_service.cloudshell_model_name}.UUID"
            attr_req = [AttributeNameValue(attr_name, new_uuid)]
            self._driver_helper_obj.api.SetServiceAttributesValues(self._driver_helper_obj.res_id,
                                                                   self._driver_helper_obj.tf_service.name, attr_req)

            # As uuid has just been created for the first time it also created a fresh entry of TF_EXEC_STATE_DATA
            self._create_tf_exec_state_data_entry(new_uuid)
            return new_uuid

    # This creates the uuid:state(statuses...) entry
    def _create_tf_exec_state_data_entry(self, uuid: str) -> None:
        current_sb_data = self._driver_helper_obj.api.GetSandboxData(self._driver_helper_obj.res_id)

        first_entry = self._generate_first_uuid_state_entry()
        new_sdkv = SandboxDataKeyValue(uuid, first_entry)
        self._add_entry_to_sandbox_data(new_sdkv)

    def _add_entry_to_sandbox_data(self, sdkv_to_add: SandboxDataKeyValue) -> None:
        self._driver_helper_obj.api.SetSandboxData(self._driver_helper_obj.res_id, [sdkv_to_add])

    def _generate_first_uuid_state_entry(self) -> str:
        first_tf_exec_status_data_entry = {
                    EXECUTE_STATUS: NONE,
                    DESTROY_STATUS: NONE
        }
        return json.dumps(first_tf_exec_status_data_entry)

    def _get_sb_data_val_by_key(self, sandbox_data: GetSandboxDataInfo, key: str):
        value = [attr.Value for attr in sandbox_data.SandboxDataKeyValues if attr.Key == key]
        if value.__len__() >= 1:
            return value[0]

    def set_status(self, status_type: str, status: str) -> None:
        uuid_sdkv_value = self._check_for_uuid_data()

        uuid_sdkv_value[status_type] = status
        updated_sdkv = SandboxDataKeyValue(self._uuid, json.dumps(uuid_sdkv_value))
        self._driver_helper_obj.api.SetSandboxData(self._driver_helper_obj.res_id, [updated_sdkv])

    def get_status(self, status_type: str) -> str:
        uuid_sdkv_value = self._check_for_uuid_data()
        return uuid_sdkv_value[status_type]

    def _check_for_uuid_data(self) -> dict:
        current_data = self._driver_helper_obj.api.GetSandboxData(self._driver_helper_obj.res_id)
        uuid_sdkv = self._get_sb_data_val_by_key(current_data, self._uuid)
        if not self._get_sb_data_val_by_key(current_data, self._uuid):
            raise Exception("Missing uuid data in sandbox data")
        return json.loads(uuid_sdkv)

