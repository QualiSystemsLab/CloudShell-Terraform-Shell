import os

from package.tests.integration_tests.helper_objects.integration_context import RealAPIIntegrationData


class RealTestsData(object):
    def __init__(self):
        self.integration_data1 = RealAPIIntegrationData(os.environ.get("SB_SERVICE_ALIAS1"))
        self.integration_data2 = RealAPIIntegrationData(os.environ.get("SB_SERVICE_ALIAS2"))

    def clear_sb_data(self):
        self.integration_data1.api.ClearSandboxData(self.integration_data1.context.reservation.reservation_id)
