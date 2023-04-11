from __future__ import annotations

from cloudshell.cp.core.request_actions.models import VmDetailsData, VmDetailsProperty


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
        for output_name, output_value in tf_outputs.items():
            if output_value.get("sensitive"):
                continue
            data.append(
                VmDetailsProperty(key=output_name, value=output_value.get("value"))
            )
        return data

    def create(self) -> VmDetailsData:

        try:
            instance_details = self._prepare_common_vm_instance_data(self._tf_outputs)
        except Exception as e:
            self._logger.exception("Failed to created VM Details:")
            details = VmDetailsData(appName=self._app_name, errorMessage=str(e))
        else:
            details = VmDetailsData(
                appName=self._app_name,
                vmInstanceData=instance_details,
                vmNetworkData=[],
            )
        self._logger.info(f"VM Details: {details}")
        return details
