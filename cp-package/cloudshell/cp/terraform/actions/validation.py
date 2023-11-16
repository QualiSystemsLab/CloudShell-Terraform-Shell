from __future__ import annotations

import os
from collections.abc import Iterable
from typing import TYPE_CHECKING
from urllib.request import urlopen

import attr

from cloudshell.cp.terraform.exceptions import (
    BaseTFException,
    InvalidAttributeException,
)

if TYPE_CHECKING:
    from logging import Logger

    from cloudshell.cp.terraform.resource_config import TerraformResourceConfig


class SwitchNotFound(BaseTFException):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Neither dvSwitch nor vSwitch with name {name} not found")


BEHAVIOURS_DURING_SAVE = ("Remain Powered On", "Power Off")


@attr.s(auto_attribs=True)
class ValidationActions:
    pass


#     _si: SiHandler
#     _resource_conf: TFResourceConfig
#     _logger: Logger
#
#     def _get_dc(self) -> DcHandler:
#         return DcHandler.get_dc(self._resource_conf.default_datacenter, self._si)
#
#     def validate_resource_conf(self):
#         self._logger.info("Validating resource config")
#         conf = self._resource_conf
#         _is_not_empty(conf.address, "address")
#         _is_not_empty(conf.user, conf.ATTR_NAMES.user)
#         _is_not_empty(conf.password, conf.ATTR_NAMES.password)
#         _is_not_empty(conf.default_datacenter, conf.ATTR_NAMES.default_datacenter)
#         _is_not_empty(conf.vm_cluster, conf.ATTR_NAMES.vm_cluster)
#         _is_not_empty(conf.vm_storage, conf.ATTR_NAMES.vm_storage)
#         _is_not_empty(conf.vm_location, conf.ATTR_NAMES.vm_location)
#         _is_value_in(
#             conf.behavior_during_save,
#             BEHAVIOURS_DURING_SAVE,
#             conf.ATTR_NAMES.behavior_during_save,
#         )
#
#     def validate_resource_conf_dc_objects(self):
#         self._logger.info("Validating resource config objects on the TF")
#         conf = self._resource_conf
#         dc = self._get_dc()
#
#         # compute_entity = dc.get_compute_entity(conf.vm_cluster)
#         # if isinstance(compute_entity, ClusterHandler):
#         #     self.validate_cluster(compute_entity)
#
#         dc.get_network(conf.holding_network)
#         dc.get_vm_folder(conf.vm_location)
#         dc.get_datastore(conf.vm_storage)
#         if conf.saved_sandbox_storage:
#             dc.get_datastore(conf.saved_sandbox_storage)
#         if conf.default_dv_switch:
#             self._validate_switch(dc, compute_entity)
#         if conf.vm_resource_pool:
#             compute_entity.get_resource_pool(conf.vm_resource_pool)
#
#     def validate_deploy_app_dc_objects(self, deploy_app):
#         self._logger.info("Validating deploy app objects on the TF")
#         self.validate_base_app_dc_objects(
#             deploy_app.vm_location, deploy_app.vm_cluster, deploy_app.vm_storage
#         )
#
#     # def validate_base_app_dc_objects(
#     #     self, vm_location: str | None, vm_cluster: str | None, vm_storage: str | None
#     # ):
#     #     dc = DcHandler.get_dc(self._resource_conf.default_datacenter, self._si)
#     #     if vm_location:
#     #         dc.get_vm_folder(vm_location)
#     #     if vm_cluster:
#     #         dc.get_compute_entity(vm_cluster)
#     #     if vm_storage:
#     #         dc.get_datastore(vm_storage)
#
#     # def validate_deploy_app(self, deploy_app: BaseTFDeployApp):
#     #     self._logger.info("Validating deploy app")
#     #
#     #     self.validate_base_app_attrs(
#     #         deploy_app.vm_cluster, deploy_app.vm_storage, deploy_app.vm_location
#     #     )
#
#     def validate_base_app_attrs(
#         self, vm_cluster: str | None, vm_storage: str | None, vm_location: str | None
#     ):
#         conf = self._resource_conf
#         _one_is_not_empty([vm_cluster, conf.vm_cluster], conf.ATTR_NAMES.vm_cluster)
#         _one_is_not_empty([vm_storage, conf.vm_storage], conf.ATTR_NAMES.vm_storage)
#         _one_is_not_empty([vm_location, conf.vm_location], conf.ATTR_NAMES.vm_location)

# def validate_deploy_app_from_vm(self, deploy_app: VMFromVMDeployApp):
#     self._logger.info("Validating deploy app from VM")
#     self.validate_app_from_vm(deploy_app.TF_vm)
#
# def validate_app_from_vm(self, vm_path: str):
#     _is_not_empty(vm_path, VMFromVMDeployApp.ATTR_NAMES.TF_vm)
#     dc = self._get_dc()
#     dc.get_vm_by_path(vm_path)
#
# def validate_deploy_app_from_template(self, deploy_app: VMFromTemplateDeployApp):
#     self._logger.info("Validating deploy app from Template")
#     self.validate_app_from_template(deploy_app.TF_template)
#
# def validate_app_from_template(self, vm_path: str):
#     _is_not_empty(vm_path, VMFromTemplateDeployApp.ATTR_NAMES.TF_template)
#     dc = self._get_dc()
#     dc.get_vm_by_path(vm_path)
#
# def validate_deploy_app_from_clone(self, deploy_app: VMFromLinkedCloneDeployApp):
#     self._logger.info("Validating deploy app from Linked Clone")
#     self.validate_app_from_clone(
#         deploy_app.TF_vm, deploy_app.TF_vm_snapshot
#     )
#
# def validate_app_from_clone(self, vm_path: str, snapshot_path: str):
#     _is_not_empty(vm_path, VMFromLinkedCloneDeployApp.ATTR_NAMES.TF_vm)
#     _is_not_empty(
#         snapshot_path, VMFromLinkedCloneDeployApp.ATTR_NAMES.TF_vm_snapshot
#     )
#     dc = self._get_dc()
#     vm = dc.get_vm_by_path(vm_path)
#     vm.get_snapshot_by_path(snapshot_path)
#
# def validate_deploy_app_from_image(self, deploy_app: VMFromImageDeployApp):
#     self._logger.info("Validating deploy app from Image")
#     self.validate_app_from_image(deploy_app.TF_image)
#
# def validate_app_from_image(self, image_url: str):
#     _is_not_empty(image_url, VMFromImageDeployApp.ATTR_NAMES.TF_image)
#     _is_valid_url(image_url, VMFromImageDeployApp.ATTR_NAMES.TF_image)
#
# def validate_ovf_tool(self, ovf_tool_path):
#     self._logger.info("Validating OVF Tool")
#     _is_not_empty(ovf_tool_path, self._resource_conf.ATTR_NAMES.ovf_tool_path)
#     _is_valid_url(ovf_tool_path, self._resource_conf.ATTR_NAMES.ovf_tool_path)
#
# @staticmethod
# def validate_cluster(cluster: ClusterHandler) -> None:
#     if not cluster.hosts:
#         raise HostNotPresentInCluster(cluster)
#
# def _validate_switch(
#     self, dc: DcHandler, compute_entity: BasicComputeEntityHandler
# ) -> None:
#     switch_name = self._resource_conf.default_dv_switch
#     try:
#         dc.get_dv_switch(switch_name)
#     except DvSwitchNotFound:
#         try:
#             compute_entity.get_v_switch(switch_name)
#         except VSwitchNotFound:
#             raise SwitchNotFound(switch_name)


def _is_valid_url(url: str, attr_name: str):
    try:
        urlopen(url)
    except Exception:
        if os.path.isfile(url):
            return True
    else:
        return True

    raise InvalidAttributeException(f"{attr_name} is invalid. Unable to access {url}")


def _is_not_empty(value: str, attr_name: str):
    if not value:
        raise InvalidAttributeException(f"{attr_name} cannot be empty")


def _is_value_in(value: str, expected_values: Iterable[str], attr_name: str):
    if value not in expected_values:
        raise InvalidAttributeException(
            f"{attr_name} should be one of the {list(expected_values)}"
        )


def _one_is_not_empty(values: list, attr_name: str):
    if not any(values):
        raise InvalidAttributeException(f"{attr_name} cannot be empty")
