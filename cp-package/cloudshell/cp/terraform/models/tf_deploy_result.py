from functools import lru_cache

from cloudshell.cp.core.request_actions.models import Attribute, VmDetailsData


class TFDeployResult:
    def __init__(self, unparsed_output_json, deploy_app, app_name, path, logger):
        self._unparsed_output_json = unparsed_output_json
        self._logger = logger
        self.deploy_app = deploy_app
        self._app_name = app_name
        self._address = None
        self._path = path
        self._attributes = []

    @property
    def path(self) -> str:
        return self._path

    @property
    @lru_cache()
    def app_name(self) -> str:
        self._get_deploy_app_attrs()
        return self._app_name

    @property
    @lru_cache()
    def address(self) -> str:
        self._get_deploy_app_attrs()
        return self._address

    @property
    @lru_cache()
    def deploy_app_attrs(self) -> list[Attribute]:
        self._get_deploy_app_attrs()
        return self._attributes

    def get_vm_details_data(self) -> VmDetailsData:
        return VmDetailsData()

    def _get_deploy_app_attrs(self):
        """Get the list of attributes to be added to the deployed app.

        :return: list of attributes
        :rtype: list[Attribute]
        """
        app_attributes = []
        outputs = []
        secret_outputs = []

        for output_name, output_params in self._unparsed_output_json.items():
            attr_name = self.deploy_app.terraform_app_outputs_map.pop(output_name)
            if attr_name:
                if attr_name.lower() == "app_name":
                    self._app_name = output_params.get("value")
                elif attr_name.lower() == "address":
                    self._address = output_params.get("value")
                else:
                    full_attr_name = self.deploy_app.full_name_attrs_map.get(attr_name)
                    app_attributes.append(Attribute(attributeName=full_attr_name,
                                                    attributeValue=output_params.get("value")))
            else:
                line = f"{output_name}: {output_params.get('value')}"
                if output_params.get("sensitive", True):
                    secret_outputs.append(line)
                else:
                    outputs.append(line)
        if outputs:
            outputs_name = self.deploy_app.get_app_resource_attribute(
                "Terraform Outputs"
            )
            full_outputs_name = self.deploy_app.full_name_attrs_map.get(outputs_name)
            if full_outputs_name:
                app_attributes.append(
                    Attribute(
                        attributeName=full_outputs_name,
                        attributeValue=",".join(outputs)
                    )
                )
        if secret_outputs:
            secret_outputs_name = self.deploy_app.get_app_resource_attribute(
                "Terraform Sensitive Outputs"
            )
            full_sec_outputs_name = self.deploy_app.full_name_attrs_map.get(
                secret_outputs_name)
            app_attributes.append(
                Attribute(
                    attributeName=full_sec_outputs_name,
                    attributeValue=",".join(secret_outputs)
                )
            )
        return app_attributes
