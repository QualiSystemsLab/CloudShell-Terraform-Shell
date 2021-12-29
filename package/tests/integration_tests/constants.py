SHELL_NAME = "Generic Terraform Service"
UUID_ATTRIBUTE = f"{SHELL_NAME}.UUID"

INT_TEST_TF_VER = "0.15.1"
INT_TEST_CLP_RESOURSE = "real_azure"


class ATTRIBUTE_NAMES:
    TF_OUTPUTS = "Terraform Outputs"
    TF_SENSIITVE_OUTPUTS = "Terraform Sensitive Outputs"
    TF_INPUTS = "Terraform Inputs"
    CT_INPUTS = "Custom Tags"
    APPLY_TAGS = "Apply Tags"
    CUSTOM_TAGS = "Custom Tags"
    REMOTE_STATE_PROVIDER = "Remote State Provider"
    GITHUB_TERRAFORM_MODULE_URL = "Github Terraform Module URL"
    TERRAFORM_VERSION = "Terraform Version"
    GITHUB_TOKEN = "Github Token"
    GITHUB_URL = "Github Terraform Module URL"
    BRANCH = "Branch"
    CLOUD_PROVIDER = "Cloud Provider"
    UUID = "UUID"

EXPECTED_VAULT_TF_OUTPUTS = "BLA1=bla1,BLA2=bla2"
EXPECTED_VAULT_TF_SENSETIVE_OUTPUTS_DEC = "SECRET_VALUE=test,SECRET_VALUE_2=my_secret"
EXPECTED_VAULT_TF_SENSETIVE_OUTPUTS_ENC = 'nwH0Qhxnn7ntDpWxsvol+89EPFFSvYE16gHjACzsQRDzvXXnNFc4WfYpgq5w1kw8'