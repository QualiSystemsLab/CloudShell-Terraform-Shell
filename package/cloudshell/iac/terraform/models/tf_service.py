import uuid

from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeNameValue
from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES


class TerraformServiceObject(object):

    def __init__(self, api: CloudShellAPISession, res_id: str, name: str, cloudshell_model_name: str):
        self.api = api
        self.res_id = res_id
        self.name = name
        self.cloudshell_model_name = cloudshell_model_name
        self.attributes = self._set_context_resource_attributes()
        self._check_uuid()

    def _check_uuid(self):
        uuid_attr_name = f"{self.cloudshell_model_name}.{ATTRIBUTE_NAMES.UUID}"
        if uuid_attr_name not in self.attributes:
            raise ValueError(f"{ATTRIBUTE_NAMES.UUID} attribute was not found")
        if not self.attributes[uuid_attr_name]:
            new_uuid = uuid.uuid4().hex
            self.attributes[uuid_attr_name] = new_uuid
            attr_req = [AttributeNameValue(uuid_attr_name, new_uuid)]
            self.api.SetServiceAttributesValues(self.res_id, self.name, attr_req)

    def _set_context_resource_attributes(self) -> dict:
        attr_dict = {}
        services = self.api.GetReservationDetails(self.res_id, disableCache=True).ReservationDescription.Services

        for service in services:
            if self.name == service.Alias:
                for attribute in service.Attributes:
                    attr_dict[attribute.Name] = attribute.Value
                return attr_dict
        raise ValueError(f"Service:{self.name} was not found in order to construct data object")
