from logging import Logger

import attr

from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


@attr.s(auto_attribs=True)
class TFPowerFlow:
    _deployed_app: VMFromTerraformGit
    _resource_config: TerraformResourceConfig
    _logger: Logger

    def _get_vm(self, si):
        self._logger.info(f"Getting VM by its UUID {self._deployed_app.vmdetails.uid}")
        # dc = DcHandler.get_dc(self._resource_config.default_datacenter, si)
        # return dc.get_vm_by_uuid(self._deployed_app.vmdetails.uid)

    def power_on(self):
        # si = SiHandler.from_config(self._resource_config, self._logger)
        vm = self._get_vm(None)

        self._logger.info(f"Powering On the {vm}")
        spec_name = vm.name
        spec = None
        # try:
        #     spec = si.get_customization_spec(spec_name)
        # except CustomSpecNotFound:
        #     self._logger.info(f"No VM Customization Spec found, powering on the {vm}")
        # else:
        #     self._logger.info(f"Adding Customization Spec to the {vm}")
        #     vm.add_customization_spec(spec)

        powered_time = vm.power_on()

        if spec:
            vm.wait_for_customization_ready(powered_time)
            # si.delete_customization_spec(spec_name)

    def power_off(self):
        # si = SiHandler.from_config(self._resource_config, self._logger)
        vm = self._get_vm(None)
        self._logger.info(f"Powering Off {vm}")
        soft = self._resource_config.shutdown_method is ShutdownMethod.SOFT
        vm.power_off(soft)
