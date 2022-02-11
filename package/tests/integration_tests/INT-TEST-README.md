# Integration Tests for CloudShell-Terraform-Shell 

The purpose of this documentation section is to provide explanations regarding different aspects of the integrations tests usage and concepts used the making.

## Content

1) Structure
2) Helper Objects/Services
3) How to:
   1) Run
   2) Extend

### Structure
 
The Integration tests are devided into two types:
1) Mocked (mock_api_based_tests)
2) Real (real_api_based_tests)

The Mocked (*1) tests will be using the Mock API (multiple patched functions of the API) during tests
for that it shall also use the MockAPIIntegrationData Object that inherits from BaseIntegrationData part of helper_objects\integration_context.py

he Real (*2) tests will be using the Real API (Communicate with an actual live CloudShell server) during tests
* for that one would need to create a int_tests_secrets.env file based on the values mentioned in int_tests_secrets.template.env
  in order for the test to work.
* In addition, one must also create a blueprint (and a derived sandbox) with two services (which the tests will use for running the tests) 
for that it shall also use the RealAPIIntegrationData Object that inherits from BaseIntegrationData part of helper_objects\integration_context.py

### Helper Objects/Services

1) Helper Object (helper_objects)
   1) Environment Variables (helper_objects\env_vars.py)
      * Used to hold generatl information regarding the Real reservation testing against
   2) Integration Context Data (helper_objects\integration_context.py)
      * Used both by "Real" and "Mocked" in order to construct the data for the tests wether real or mocked 
2) Helper Services (helper_services)
   1) Serice Attributes Factory (helper_services\service_attributes_factory.py)
      * Used by "Mocked" tests to create empty attributes

### How To

#### Run
prerequisite: have a a unit tests plugin installed (e.g. unittests)

   1) As IDEs have sometimes issues with importing packages, best way is to open the project from it`s "Package" as root dir
   2) For running real tests:
      1) Instantiate a CloudShell server
      2) Create a blueprint with two TF Services
      3) create a int_tests_secrets.env file and fill it with the variables (and their values) from int_tests_secrets.template.env
   3) For mock tests:
      1) either from IDE or CLI : python -m unittest discover -p "int_test_mock*.py"
      
#### Extend

Test cases part of int_test_mock_tf_execute_destroy.py have several sections:

1) Patching (bypassing the use of real api / server requirements):

 For example:

    @patch('cloudshell.iac.terraform.services.tf_proc_exec.TfProcExec.can_destroy_run')
    @patch('cloudshell.iac.terraform.terraform_shell.SandboxDataHandler')
    @patch('cloudshell.iac.terraform.services.object_factory.CloudShellSessionContext')
      
2) Making sure the patched functions/objects are initialized with the right values:

 For example:

    def test_execute_and_destroy_azure_vault(self, patch_api, patched_sbdata_handler, can_destroy_run):

        can_destroy_run.return_value = True

        patch_api.return_value.get_api.return_value = self.mock_api

        mock_sbdata_handler = Mock()
        mock_sbdata_handler.get_tf_working_dir = self._get_mocked_tf_working_dir
        mock_sbdata_handler.set_tf_working_dir = self._set_mocked_tf_working_dir
        patched_sbdata_handler.return_value = mock_sbdata_handler

3) the run_execute_and_destroy function that holds 3 parameters
   what function needs to run before executing
      * create such a function and modify the attributes values there, so it will match the test case requirements here 
   what function needs to run before destroying
   The data used for the test (self.integration_data1)

 For example:

self.run_execute_and_destroy(
            pre_exec_function=self.pre_exec_azure_vault,
            pre_destroy_function=self.pre_destroy,
            integration_data=self.integration_data1
        )