from __future__ import annotations

from abc import ABC, abstractmethod

from cloudshell.cp.terraform import constants
from cloudshell.cp.terraform.flows.get_attribute_hints import attribute_hints
# from cloudshell.cp.terraform.handlers.dc_handler import DcHandler
from cloudshell.cp.terraform.models.DeployDataHolder import DeployDataHolder


class AbstractHintsHandler(ABC):
    @property
    @staticmethod
    @abstractmethod
    def DEPLOYMENT_PATH() -> str:
        pass

    @property
    @staticmethod
    @abstractmethod
    def ATTRIBUTES() -> tuple[type[attribute_hints.AbstractAttributeHint]]:
        pass

    def __init__(self, request: DeployDataHolder,):
        self._request = request

    def prepare_hints(self) -> list[dict]:
        hints = []
        requested_attribute = next(
            (
                attr
                for attr in self.ATTRIBUTES
                if self._request.AttributeName.endswith(f".{attr.ATTR_NAME}")
            ),
            None,
        )
        if requested_attribute:
            return [requested_attribute(self._request, self._dc).prepare_hints()]
        return hints


class VMfromTFGITHintsHandler(AbstractHintsHandler):
    DEPLOYMENT_PATH = constants.VM_FROM_TF_GIT
    ATTRIBUTES = (
        attribute_hints.TFVMAttributeHint,
        attribute_hints.VMClusterAttributeHint,
        attribute_hints.VMStorageAttributeHint,
    )


def get_handler(request: DeployDataHolder) -> AbstractHintsHandler:
    handlers = (
        VMfromTFGITHintsHandler
    )

    for handler in handlers:
        if request.DeploymentPath == handler.DEPLOYMENT_PATH:
            return handler(request)

    raise Exception(
        f"Unable to process deployment path '{request.DeploymentPath}'. "
        f"It should be one of: {[handler.DEPLOYMENT_PATH for handler in handlers]}"
    )
