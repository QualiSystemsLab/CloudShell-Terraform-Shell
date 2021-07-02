import os
from typing import List
from unittest import mock
from unittest.mock import Mock

from cloudshell.api.cloudshell_api import SandboxDataKeyValue
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import ResourceCommandContext
from dotenv import load_dotenv

from data_model import TerraformService2G
from driver import TerraformService2GDriver
from driver_helper_obj import DriverHelperObject
from tests.constants import SHELL_NAME


class UnitTestsData(object):
    def __init__(self):
        # used to mock sandbox data
        self._sdkv_list = []

        self._prepare_context()
        self.logger = get_qs_logger(log_group=self.context.resource.name)
        self._create_driver()
        self.prepare_api()
        self.prepare_driver_helper()

    def prepare_driver_helper(self):
        service_resource = TerraformService2G.create_from_context(self.context)
        self.driver_helper = DriverHelperObject(
            self.mock_api,
            self.context.reservation.reservation_id,
            service_resource,
            self.logger)

    def _prepare_context(self):
        load_dotenv()
        self.context = mock.create_autospec(ResourceCommandContext)

        self.context.connectivity = mock.MagicMock()

        self.context.resource = mock.MagicMock()
        self.context.resource.attributes = dict()
        self.context.resource.name = "service_test"

        self.context.reservation = mock.MagicMock()
        self.context.reservation.reservation_id = os.environ.get("RESERVATION_ID")
        self.context.reservation.domain = os.environ.get("RESERVATION_DOMAIN")

        self.context.resource.attributes[f"{SHELL_NAME}.Github Token"] = os.environ.get("GH_TOKEN")
        self.context.resource.attributes[f"{SHELL_NAME}.Cloud Provider"] = os.environ.get("CLP_RESOURCE")
        self.context.resource.attributes[f"{SHELL_NAME}.Terraform Version"] = os.environ.get("TFEXEC_VERSION")

    def set_attribute(self, attribute_name: str, attribute_value: str):
        self.context.resource.attributes[f"{SHELL_NAME}.{attribute_name}"] = attribute_value

    def prepare_api(self, resource_model: str = "", resource_family: str = "", mock_resource_attributes: List = None):
        if mock_resource_attributes is None:
            mock_resource_attributes = []
        self.mock_api = Mock()

        self.mock_api.DecryptPassword = _decrypt_password
        self.mock_api.GetSandboxData = self._get_sb_data
        self.mock_api.SetSandboxData = self._set_sb_data

        mock_resource_details = Mock()
        mock_resource_details.ResourceModelName = resource_model
        mock_resource_details.ResourceFamilyName = resource_family

        self.mock_api.GetResourceDetails.return_value = mock_resource_details

        mock_resource_attributes = mock_resource_attributes

        self.mock_api.GetResourceDetails.return_value.ResourceAttributes = mock_resource_attributes

    def _set_sb_data(self, resid: str, sdkv_list: List[SandboxDataKeyValue]) -> None:
        self._sdkv_list = sdkv_list

    def _get_sb_data(self, resid: str):
        mock_sdb = Mock()
        mock_sdb.SandboxDataKeyValues = self._sdkv_list
        return mock_sdb

    def _create_driver(self):
        self.driver = TerraformService2GDriver()
        self.driver.initialize(self.context)


def _decrypt_password(x):
    result = mock.MagicMock()
    result.Value = x
    return result


'''         
        mock_resource_details.ResourceModelName = "Microsoft Azure"
        mock_resource_details.ResourceFamilyName = "Cloud Provider"


        mock_resource_attributes = [Mock(Name="Azure Subscription ID", Value="ARM_SUBSCRIPTION_ID_MOCKVALUE"),
                                    Mock(Name="Azure Tenant ID", Value="ARM_TENANT_ID_MOCKVALUE"),
                                    Mock(Name="Azure Application ID", Value="ARM_CLIENT_ID_MOCKVALUE"),
                                    Mock(Name="Azure Application Key", Value="ARM_CLIENT_SECRET_MOCKVALUE")]
'''