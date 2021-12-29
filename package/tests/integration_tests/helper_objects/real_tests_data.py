import os
from unittest.mock import Mock

from package.tests.integration_tests.helper_objects.integration_context import MockAPIIntegrationData, \
    RealAPIIntegrationData
from package.tests.integration_tests.helper_services.service_attributes_factory import ServiceAttributesMockBuilder

from cloudshell.api.cloudshell_api import NameValuePair

class RealTestsData(object):
    def __init__(self):
        self.integration_data1 = RealAPIIntegrationData(os.environ.get("SB_SERVICE_ALIAS1"))
        self.integration_data2 = RealAPIIntegrationData(os.environ.get("SB_SERVICE_ALIAS2"))

    def clear_sb_data(self):
        self.integration_data1.api.ClearSandboxData(self.integration_data1.context.reservation.reservation_id)