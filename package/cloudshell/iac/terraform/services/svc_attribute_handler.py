from cloudshell.api.cloudshell_api import CloudShellAPISession


class ServiceAttrHandler(object):
    def __init__(self, api: CloudShellAPISession, sandbox_id: str, tf_service: any):
        self._api = api
        self._sandbox_id = sandbox_id
        self._tf_service = tf_service
        self._attributes = {}
        self._populate_attr_list()

    def get_attribute(self, attribute_name: str) -> str:
        if attribute_name in self._attributes:
            return self._attributes[attribute_name]
        return ""

    def _populate_attr_list(self):
        services = self._api.GetReservationDetails(self._sandbox_id).ReservationDescription.Services
        for service in services:
            if service.Alias == self._tf_service.name:
                for attribute in service.Attributes:
                    if "." in attribute.Name:
                        self._attributes[attribute.Name.split(".")[1]] = attribute.Value
                    else:
                        self._attributes[attribute.Name] = attribute.Value
