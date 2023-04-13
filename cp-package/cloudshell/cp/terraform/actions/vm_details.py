from __future__ import annotations

from typing import TYPE_CHECKING

from cloudshell.cp.core.request_actions.models import VmDetailsData, VmDetailsProperty

if TYPE_CHECKING:
    from cloudshell.cp.terraform.models.tf_deploy_result import TFDeployResult


class VMDetailsActions:
    def __init__(
        self,
        resource_config,
        app_name,
        tf_outputs,
        path,
        logger,
    ):
        self._resource_conf = resource_config
        self._app_name = app_name
        self._tf_outputs = tf_outputs
        self._path = path
        self._logger = logger

    @staticmethod
    def _prepare_common_vm_instance_data(tf_outputs: dict) -> list[VmDetailsProperty]:
        data = []
        for output, output_data in tf_outputs.items():
            if output_data.get("sensitive"):
                continue
            data.append(
                VmDetailsProperty(key=output, value=output_data.get("value"))
            )
        return data

    def create(self) -> VmDetailsData:
        details = VMDetailsActions._prepare_common_vm_instance_data(self._tf_outputs)
        self._logger.info(f"VM Details: {details}")
        return VmDetailsData(
            vmInstanceData=details,
            vmNetworkData=[],
            appName=self._app_name,
        )
