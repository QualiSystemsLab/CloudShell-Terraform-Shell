from logging import Logger

import attr

from cloudshell.shell.core.driver_context import AutoLoadDetails

# from cloudshell.cp.terraform.actions.validation import ValidationActions
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


@attr.s(auto_attribs=True)
class TFAutoloadFlow:
    _resource_config: TerraformResourceConfig
    _logger: Logger

    def discover(self) -> AutoLoadDetails:
        si = SiHandler.from_config(self._resource_config, self._logger)
        validation_actions = ValidationActions(si, self._resource_config, self._logger)
        validation_actions.validate_resource_conf()
        validation_actions.validate_resource_conf_dc_objects()

        dc = DcHandler.get_dc(self._resource_config.default_datacenter, si)
        deployed_apps_folder_path = TFPath(self._resource_config.vm_location)
        deployed_apps_folder_path.append(DEPLOYED_APPS_FOLDER)
        deployed_apps_folder = dc.get_or_create_vm_folder(deployed_apps_folder_path)

        vsphere_client = VSphereSDKHandler.from_config(
            resource_config=self._resource_config,
            reservation_info=None,
            logger=self._logger,
            si=si,
        )
        if vsphere_client is not None:
            vsphere_client.create_categories()
            tags = TFTagsManager.get_tags_created_by()
            vsphere_client.assign_tags(deployed_apps_folder, tags)

        return AutoLoadDetails([], [])
