from unittest.mock import patch, Mock
from dotenv import load_dotenv

import os
from unittest import TestCase
from pathlib import Path

from package.tests.integration_tests.helper_services.mock_tests_prepper import pre_exec_azure_vault, pre_destroy
from package.tests.integration_tests.helper_objects.mock_tests_data import MockTestsData

from package.tests.constants import MOCK_ALIAS1

from package.tests.integration_tests.constants import SHELL_NAME, ATTRIBUTE_NAMES, EXPECTED_VAULT_TF_OUTPUTS, \
    EXPECTED_VAULT_TF_SENSETIVE_OUTPUTS_DEC


class TestMockTerraformExecuteDestroy(TestCase):
    @classmethod
    def setUpClass(self):
        print(os.getcwd())
        load_dotenv(Path('../int_tests.env'))
        if os.path.isfile(Path('../int_tests_secrets.env')):
            load_dotenv(Path('../int_tests_secrets.env'))

    @patch('cloudshell.iac.terraform.services.object_factory.CloudShellSessionContext')
    def setUp(self, patched_api) -> None:
        self.test_data_object = MockTestsData()
        patched_api.return_value.get_api.return_value = self.test_data_object.mock_api
        self.test_data_object.prepare_integration_data()

    '''------------------------------ Test Cases ---------------------------------'''

    @patch('cloudshell.iac.terraform.services.tf_proc_exec.TfProcExec.can_destroy_run')
    @patch('cloudshell.iac.terraform.terraform_shell.SandboxDataHandler')
    @patch('cloudshell.iac.terraform.services.object_factory.CloudShellSessionContext')
    def test_execute_and_destroy_azure_vault(self, patch_api, patched_sbdata_handler, can_destroy_run):
        can_destroy_run.return_value = True
        patch_api.return_value.get_api.return_value = self.test_data_object.mock_api
        mock_sbdata_handler = Mock()
        mock_sbdata_handler.get_tf_working_dir = self.test_data_object._get_mocked_tf_working_dir
        mock_sbdata_handler.set_tf_working_dir = self.test_data_object._set_mocked_tf_working_dir
        patched_sbdata_handler.return_value = mock_sbdata_handler

        pre_exec_azure_vault(self.test_data_object)
        self.test_data_object.integration_data1.tf_shell.execute_terraform()

        self.assertTrue(self.are_vault_tf_outputs_correct())
        pre_destroy(self.test_data_object.integration_data1)
        self.test_data_object.integration_data1.tf_shell.destroy_terraform()

    def are_vault_tf_outputs_correct(self):
        tf_outputs_correct = False
        tf_sensitive_outputs_correct = False
        try:
            for call in self.test_data_object.mock_api.SetServiceAttributesValues.call_args_list:
                if call.args[1] == MOCK_ALIAS1:
                    for attribute_name_value in call.args[2]:
                        if attribute_name_value.Name == f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_OUTPUTS}" and \
                                attribute_name_value.Value == EXPECTED_VAULT_TF_OUTPUTS:
                            tf_outputs_correct = True
                        if attribute_name_value.Name == f"{SHELL_NAME}.{ATTRIBUTE_NAMES.TF_SENSIITVE_OUTPUTS}" and \
                                attribute_name_value.Value == EXPECTED_VAULT_TF_SENSETIVE_OUTPUTS_DEC:
                            tf_sensitive_outputs_correct = True
        except Exception as e:
            raise
        return tf_outputs_correct and tf_sensitive_outputs_correct
