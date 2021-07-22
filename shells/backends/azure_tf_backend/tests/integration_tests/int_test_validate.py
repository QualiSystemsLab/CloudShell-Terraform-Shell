from unittest2 import TestCase

from tests.integration_tests.helper_objects.integration_context import IntegrationData


class TestTerraformBackend(TestCase):
    def setUp(self):
        self.integration_data = IntegrationData()

    def test_get_inventory(self):
        self.integration_data.driver.get_inventory(self.integration_data.context)
