from cloudshell.cp.core.request_actions.models import DeployAppResult

from cloudshell.cp.terraform.models.tf_deploy_result import TFDeployResult


class TFDeployAppResult(DeployAppResult):

    @classmethod
    def from_tf_deploy_result(cls, tf_deploy_result: TFDeployResult):
        return DeployAppResult(
            actionId=tf_deploy_result.deploy_app.actionId,
            vmUuid=tf_deploy_result.path,
            vmName=tf_deploy_result.app_name,
            deployedAppAddress=tf_deploy_result.address or "",
            vmDetailsData=tf_deploy_result.get_vm_details_data,
            deployedAppAdditionalData={},
            deployedAppAttributes=tf_deploy_result.deploy_app_attrs,
            # deployedAppAttributes=[
            #     Attribute(
            #         attributeName="Terraform DeployedApp 2G.Terraform Outputs",
            #         attributeValue=json.dumps(execution_outputs[0])),
            #     Attribute(
            #         attributeName="Terraform DeployedApp 2G.Terraform Sensitive Outputs",
            #         attributeValue=json.dumps(execution_outputs[1]))
            #     ],
        )
