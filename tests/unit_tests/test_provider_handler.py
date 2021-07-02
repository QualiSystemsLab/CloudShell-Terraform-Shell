from unittest import TestCase
from subprocess import Popen, PIPE
from unittest.mock import Mock

from services.provider_handler import ProviderHandler
from dotenv import load_dotenv

from tests.unit_tests.helpers.unit_tests_data import UnitTestsData

load_dotenv()


class ProviderHandlerTest(TestCase):
    def setUp(self) -> None:
        self.data = UnitTestsData()

    def test_initialize_provider(self):
        mock_resource_attributes = [Mock(Name="Azure Subscription ID", Value="ARM_SUBSCRIPTION_ID_MOCKVALUE"),
                                    Mock(Name="Azure Tenant ID", Value="ARM_TENANT_ID_MOCKVALUE"),
                                    Mock(Name="Azure Application ID", Value="ARM_CLIENT_ID_MOCKVALUE"),
                                    Mock(Name="Azure Application Key", Value="ARM_CLIENT_SECRET_MOCKVALUE")]

        self.data.prepare_api("Microsoft Azure", "Cloud Provider", mock_resource_attributes)

        self.data.prepare_driver_helper()
        self.data.driver_helper.tf_service.cloud_provider = Mock()

        ProviderHandler.initialize_provider(self.data.driver_helper)

        self._validate_env_var("%ARM_SUBSCRIPTION_ID%", "ARM_SUBSCRIPTION_ID_MOCKVALUE")
        self._validate_env_var("%ARM_TENANT_ID%", "ARM_TENANT_ID_MOCKVALUE")
        self._validate_env_var("%ARM_CLIENT_ID%", "ARM_CLIENT_ID_MOCKVALUE")
        self._validate_env_var("%ARM_CLIENT_SECRET%", "ARM_CLIENT_SECRET_MOCKVALUE")

    def _validate_env_var(self, var, value):
        process = Popen(['echo', var], stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        print(f"var={var} output={stdout.decode('utf-8').rstrip()} value={value}")
        self.assertEqual(stdout.decode("utf-8").rstrip(), value)
