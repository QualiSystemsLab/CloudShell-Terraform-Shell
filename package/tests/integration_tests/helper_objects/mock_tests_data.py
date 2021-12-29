import os
from unittest.mock import Mock

from package.tests.integration_tests.helper_objects.integration_context import MockAPIIntegrationData
from package.tests.integration_tests.helper_services.service_attributes_factory import ServiceAttributesMockBuilder

from cloudshell.api.cloudshell_api import NameValuePair, AttributeNameValue


class MockTestsData(object):
    def __init__(self):
        self.mock_api = Mock()
        self.service1 = Mock()
        self.service2 = Mock()
        self._mocked_tf_working_dir = ''
        self.service1.Alias = ''
        self.service1.Attributes = None
        self.service2.Alias = ''
        self.service2.Attributes = None

        self._prepare_mock_services()
        self._prepare_mock_api()

    def prepare_integration_data(self):
        self.integration_data1 = MockAPIIntegrationData(self.service1.Alias, self.mock_api)
        self.integration_data2 = MockAPIIntegrationData(self.service2.Alias, self.mock_api)

    def _prepare_mock_services(self):
        self.service1 = Mock()
        self.service1.Alias = "MOCK_ALIAS1"
        self.service1.Attributes = ServiceAttributesMockBuilder.create_empty_attributes()
        self.service2 = Mock()
        self.service2.Alias = "MOCK_ALIAS2"
        self.service2.Attributes = ServiceAttributesMockBuilder.create_empty_attributes()

    def _prepare_mock_api(self):
        self.mock_api = Mock()
        self.mock_api.DecryptPassword = _decrypt_password
        self.mock_api.GetReservationDetails.return_value.ReservationDescription.Services = [self.service1,
                                                                                            self.service2]

        # self.mock_api.SetServiceAttributesValues = self._set_service_attributes_values

        self.mock_api.GetResourceDetails.return_value.ResourceFamilyName = 'Cloud Provider'
        self.mock_api.GetResourceDetails.return_value.ResourceModelName = 'Microsoft Azure'
        self.mock_api.GetResourceDetails.return_value.ResourceAttributes = [
            NameValuePair(Name="Azure Subscription ID", Value=os.environ.get("AZURE_SUBSCRIPTION_ID")),
            NameValuePair(Name="Azure Tenant ID", Value=os.environ.get("AZURE_TENANT_ID")),
            NameValuePair(Name="Azure Application ID", Value=os.environ.get("AZURE_APPLICATION_ID")),
            NameValuePair(Name="Azure Application Key", Value=os.environ.get("AZURE_APPLICATION_KEY_DEC"))
        ]

    def _get_mocked_tf_working_dir(self):
        return self._mocked_tf_working_dir

    def _set_mocked_tf_working_dir(self, tf_working_dir: str):
        self._mocked_tf_working_dir = tf_working_dir

    '''
    @staticmethod
    def _set_service_attributes_values(sandbox_id: str, tf_service_name: str,
                                       attr_update_req: list[AttributeNameValue]):
        print("")
        pass
    '''

def _decrypt_password(x):
    result = Mock()
    result.Value = x
    return result

