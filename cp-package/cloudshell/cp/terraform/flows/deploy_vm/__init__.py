from __future__ import annotations

# from .base_flow import AbstractTFDeployVMFlow
# from .from_image import TFDeployVMFromImageFlow
# from .from_linked_clone import TFDeployVMFromLinkedCloneFlow
# from .from_template import TFDeployVMFromTemplateFlow
# from .from_vm import TFDeployVMFromVMFlow

from cloudshell.cp.terraform.models import deploy_app

# DEPLOY_APP_TO_FLOW = (
#     (deploy_app.VMFromLinkedCloneDeployApp, TFDeployVMFromLinkedCloneFlow),
#     (deploy_app.VMFromVMDeployApp, TFDeployVMFromVMFlow),
#     (deploy_app.VMFromImageDeployApp, TFDeployVMFromImageFlow),
#     (deploy_app.VMFromTemplateDeployApp, TFDeployVMFromTemplateFlow),
# )


# def get_deploy_flow(request_action) -> type[AbstractTFDeployVMFlow]:
#     da = request_action.deploy_app
#     for deploy_class, deploy_flow in DEPLOY_APP_TO_FLOW:
#         if isinstance(da, deploy_class):
#             return deploy_flow
#     raise NotImplementedError(f"Not supported deployment type {type(da)}")


# __all__ = (
#     # TFDeployVMFromVMFlow,
#     # TFDeployVMFromImageFlow,
#     # TFDeployVMFromTemplateFlow,
#     # TFDeployVMFromLinkedCloneFlow,
#     # get_deploy_flow,
# )
