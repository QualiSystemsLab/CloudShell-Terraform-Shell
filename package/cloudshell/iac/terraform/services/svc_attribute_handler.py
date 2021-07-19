from cloudshell.api.cloudshell_api import CloudShellAPISession


class ServiceAttrHandler(object):
    def __init__(self, api: CloudShellAPISession, sandbox_id: str, tf_service: any):
        self._api = api
        self._sandbox_id = sandbox_id
        self._tf_service = tf_service

    def get_attribute(self, attribute_name: str):
        services = self._api.GetReservationDetails(self._sandbox_id).ReservationDescription.Services
        for service in services:
            if service.Alias == self._tf_service.name:
                for attribute in service.Attributes:
                    if attribute.Name == f"{self._tf_service.cloudshell_model_name}.{attribute_name}":
                        return attribute.Value
        return ""
