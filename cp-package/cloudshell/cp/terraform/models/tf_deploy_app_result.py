from cloudshell.cp.core.request_actions.models import DeployAppResult
from cloudshell.cp.terraform.models.tf_deploy_result import TFDeployResult
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


class TFDeployAppResult(DeployAppResult):
    @classmethod
    def from_tf_deploy_result(
        cls, resource_config: TerraformResourceConfig, tf_deploy_result: TFDeployResult
    ):
        return DeployAppResult(
            actionId=tf_deploy_result.deploy_app.actionId,
            vmUuid=tf_deploy_result.path,
            vmName=tf_deploy_result.app_name,
            deployedAppAddress=tf_deploy_result.address or "",
            vmDetailsData=tf_deploy_result.get_vm_details_data(
                resource_config=resource_config,
            ),
            deployedAppAdditionalData={},
            deployedAppAttributes=tf_deploy_result.deploy_app_attrs,
        )
