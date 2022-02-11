from dotenv import load_dotenv

from package.tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES, EXPECTED_VAULT_TF_OUTPUTS, \
    EXPECTED_VAULT_TF_SENSETIVE_OUTPUTS_ENC
from package.tests.integration_tests.helper_objects.real_tests_data import RealTestsData
from package.tests.integration_tests.helper_services.real_tests_prepper import pre_exec_azure_vault, \
    pre_exec_azure_vault_with_remote_access_key_based, pre_exec_azure_vault_with_remote_cloud_cred_based, \
    pre_exec_azure_vault_with_remote_invalid_nonexistent, pre_exec_azure_vault_with_remote_invalid_wrong, \
    post_vault_cleanup

import os
from pathlib import Path
from unittest import TestCase

from package.tests.integration_tests.helper_objects.integration_context import RealAPIIntegrationData


class TestRealTerraformExecuteDestroy(TestCase):
    @classmethod
    def setUpClass(self):
        load_dotenv(Path('../int_tests.env'))
        if os.path.isfile(Path('../int_tests_secrets.env')):
            load_dotenv(Path('../int_tests_secrets.env'))

    def setUp(self) -> None:
        self.test_data_object = RealTestsData()

    '''------------------------------ Test Cases ---------------------------------'''

    # To be used with any preconfigured attributes set on the service in real CS instance
    def test_execute_and_destroy(self):
        self.test_data_object.clear_sb_data()
        self.test_data_object.integration_data1.tf_shell.execute_terraform()
        self.test_data_object.integration_data1.set_context_resource_attributes_from_cs(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}")
        self.test_data_object.integration_data1.tf_shell.destroy_terraform()

    def est_execute_and_destroy_azure_vault(self):
        self.test_data_object.clear_sb_data()
        pre_exec_azure_vault(self.test_data_object.integration_data1)
        self.test_data_object.integration_data1.tf_shell.execute_terraform()
        self.test_data_object.integration_data1.set_context_resource_attributes_from_cs(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}")
        self.assertTrue(self.are_vault_tf_outputs_correct(self.test_data_object.integration_data1))
        self.test_data_object.integration_data1.tf_shell.destroy_terraform()

    '''
    def test_execute_dual_mssql(self):
        self.clear_sb_data()
        try:
            self.run_execute(pre_exec_function=self.pre_exec_azure_mssql, integration_data=self.test_data_object.integration_data1)
        except Exception as e:
            pass
        try:
            self.run_execute(pre_exec_function=self.pre_exec_azure_mssql, integration_data=self.test_data_object.integration_data2)
        except Exception as e:
            print("Error")
            pass
        self.run_destroy(pre_destroy_function=self.pre_destroy, integration_data=self.test_data_object.integration_data1)
        self.run_execute(pre_exec_function=self.pre_exec_azure_mssql, integration_data=self.test_data_object.integration_data2)
    '''

    def test_execute_and_destroy_azure_vault_with_remote_access_key_based(self):
        self.test_data_object.clear_sb_data()
        pre_exec_azure_vault_with_remote_access_key_based(self.test_data_object.integration_data1)
        self.test_data_object.integration_data1.tf_shell.execute_terraform()
        self.test_data_object.integration_data1.set_context_resource_attributes_from_cs(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}")
        self.assertTrue(self.are_vault_tf_outputs_correct(self.test_data_object.integration_data1))
        self.test_data_object.integration_data1.tf_shell.destroy_terraform()
        post_vault_cleanup(self.test_data_object.integration_data1)

    def test_execute_and_destroy_azure_vault_with_remote_access_cloud_cred_based(self):
        self.test_data_object.clear_sb_data()
        pre_exec_azure_vault_with_remote_cloud_cred_based(self.test_data_object.integration_data1)
        self.test_data_object.integration_data1.tf_shell.execute_terraform()
        self.test_data_object.integration_data1.set_context_resource_attributes_from_cs(
            f"{SHELL_NAME}.{ATTRIBUTE_NAMES.UUID}")
        self.assertTrue(self.are_vault_tf_outputs_correct(self.test_data_object.integration_data1))
        self.test_data_object.integration_data1.tf_shell.destroy_terraform()
        post_vault_cleanup(self.test_data_object.integration_data1)

    def test_execute_azure_vault_with_remote_invalid_nonexistent(self):
        self.test_data_object.clear_sb_data()
        pre_exec_azure_vault_with_remote_invalid_nonexistent(self.test_data_object.integration_data1)
        with self.assertRaises(ValueError):
            self.test_data_object.integration_data1.tf_shell.execute_terraform()
        post_vault_cleanup(self.test_data_object.integration_data1)
        print("")

    def test_execute_and_destroy_azure_vault_with_remote_invalid_wrong(self):
        self.test_data_object.clear_sb_data()
        pre_exec_azure_vault_with_remote_invalid_wrong(self.test_data_object.integration_data1)
        with self.assertRaises(ValueError):
            self.test_data_object.integration_data1.tf_shell.execute_terraform()
        post_vault_cleanup(self.test_data_object.integration_data1)
        print("")

    @staticmethod
    def are_vault_tf_outputs_correct(integration_data: RealAPIIntegrationData):
        tf_outputs_correct = False
        tf_sensitive_outputs_correct = False
        attrs = integration_data.tf_shell.get_tf_service().attributes
        try:
            if attrs[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_OUTPUTS}"] == EXPECTED_VAULT_TF_OUTPUTS:
                tf_outputs_correct = True
            if attrs[f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_SENSIITVE_OUTPUTS}"] == EXPECTED_VAULT_TF_SENSETIVE_OUTPUTS_ENC:
                tf_sensitive_outputs_correct = True
        except Exception as e:
            raise
        return tf_outputs_correct and tf_sensitive_outputs_correct
