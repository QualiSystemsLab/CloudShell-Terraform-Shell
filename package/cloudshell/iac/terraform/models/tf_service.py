from cloudshell.api.cloudshell_api import CloudShellAPISession


class TerraformServiceObject(object):

    def __init__(self, api: CloudShellAPISession, res_id: str, name: str, cloudshell_model_name: str):
        self.api = api
        self.res_id = res_id
        self.name = name
        self.cloudshell_model_name = cloudshell_model_name

        self.attributes = self.set_context_resource_attributes()

    def set_context_resource_attributes(self) -> dict:
        attr_dict = {}
        services = self.api.GetReservationDetails(self.res_id).ReservationDescription.Services
        for service in services:
            if self.name == service.Alias:
                for attribute in service.Attributes:
                    attr_dict[attribute.Name] = attribute.Value
        return attr_dict


