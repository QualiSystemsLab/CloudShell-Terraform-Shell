TERRAFORM_URL = "https://releases.hashicorp.com/terraform"

TERRAFORM_LATEST_URL = "https://checkpoint-api.hashicorp.com/v1/check/terraform"

# OS types defined by sys.platform
OS_TYPES = {
 'darwin': 'darwin_amd64',
 'linux': 'linux_amd64',
 'win32': 'windows_amd64'
 }
ERROR_LOG_LEVEL = 40
INFO_LOG_LEVEL = 20

SHELL_NAME = "Terraform Service 2G"
# GITHUB_TF_FOLDER_LINK = "https://github.com/qualidan/terraform/blob/main/test/a/b/c/hello.tf"
GITHUB_TF_FOLDER_LINK = "https://github.com/alexazarh/Colony-experiments/blob/master/terraform/azure-vault/main.tf"
TERRAFORM_FILE = "hello.tf"
TERRAFORM_EXEC_FILE = "terraform.exe"

EXECUTE_STATUS = "EXECUTE_STATUS"
DESTROY_STATUS = "DESTROY_STATUS"
APPLY_PASSED = "APPLY_PASSED"
APPLY_FAILED = "APPLY_FAILED"
PLAN_FAILED = "PLAN_FAILED"
INIT_FAILED = "INIT_FAILED"
DESTROY_FAILED = "DESTROY_FAILED"
DESTROY_PASSED = "DESTROY_PASSED"
NONE = "NONE"

DIRTY_CHARS = r'''
                \x1B  # ESC
                (?:   # 7-bit C1 Fe (except CSI)
                    [@-Z\\-_]
                |     # or [ for CSI, followed by a control sequence
                    \[
                    [0-?]*  # Parameter bytes
                    [ -/]*  # Intermediate bytes
                    [@-~]   # Final byte
                )
            '''
