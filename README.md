# CloudShell-Terraform-Shell
Purpose: allows the execution of a Terraform deployment from CloudShell. Multiple Terraform services can be added to a Blueprint or Sandbox, and these can be executed from CloudShell Portal UI by the user that is reserving the Blueprint.

Additional workflow recommendation: it is very easy to customize a Blueprint setup script that will run the “Execute Terraform” command on the service. A similar teardown script is available that will run the “Destroy Terraform” command. This way the Terraform Module lifecycle is connected to the Sandbox lifecycle.

## Content
1. cloudshell-iac-terraform - Primary Package <br>
   Python package that contains all of the logic. It's assumed that this python package is used by a CloudShell Service 
2. generic_terraform_service - Main Shell <br>
   Use as is in a generic fashion or use it as an example to build an extension for a specific purpose (e.g. Azure MsSql, AWS RDS or any other managed cloud service)
3. Remote backends: <br>
   azure_tf_backend - Azure Remote Backend shell. See below for more details about usage 

## Shell Usage Instructions
 
1. Import Shell(/s) to CloudShell “Shells” screen.
2. Add Terraform Service to Blueprint/Sandbox.
3. Configure the different attributes to match the requirement of the deployment. Please see below the documentation per attribute.

## Service Attributes (generic_terraform_service)
|Attribute Name|Data Type|Description|Mandatory?|
|:---|:---|:---|:---|
|Github Terraform Module URL|String|Path to target module. Can be provided in three formats: <br/> 1) https://github.com/ACCOUNT/REPO/tree/BRANCH/PATH_TO_FOLDER <br/> 2) https://github.com/ACCOUNT/REPO/blob/BRANCH/PATH_TO_FOLDER/FILENAME.tf <br/> 3) https://raw.githubusercontent.com/ACCOUNT/REPO/BRANCH/PATH_TO_FOLDER/FILENAME.tf  | Yes |
|Terraform Version|String|The version of terraform.exe that will be downloaded and used (If not specified latest version will be used)|  No |
|Github Token|String| Github PAT (Private Access Token) to be used in order to download TF module. The entire repo will be downloaded and then the referenced TF module will be executed |  Yes |
|Cloud Provider|String| Reference to the CloudProvider resource that should be used to initialize the Terrafom provider. Supported cloud providers: <br> - Azure Shell <br>- Azure Shell 2G| Yes |
|Branch|String| In case specified will override the branch in the Github Terraform Module URL |  No |
|Terraform Outputs|String| Unmapped and *non-sensitive* TF outputs will be stored as a CSV list of key value pairs on this attribute. This attribute is optional. |  No |
|Terraform Sensitive Outputs|Password| Unmapped and *sensitive* TF outputs will be stored as a CSV list of key value pairs on this attribute. This attribute must be of type "password. The attribute is optional. |  No |
|Terraform Inputs|String|CSV list of key value pairs to specify values for TF variables (e.g. varname1=varvalue1,varname2=varvalue2...)| No |
|Remote State Provider|String|Reference a Remote State Provider resource to add a remote backend to your TF module. The remote backend definition will be added automatically to the TF module. Use this functionality to store the *tfstate* file in a secure location. <br/>If not specified, the *tf_state* file will be kept locally on the execution server in a temp directory and will be removed only after a successful destroy. This is considered less secure and should be used for development purposes only|  No |
|Apply Tags|Boolean|Specify whether TF resources will be auto-tagged. 6 default tags will be added automatically and also any custom tags will be added to all TF resources|  N/A|
|Custom Tags|String|Comma separated list of name=value pairs to be used as additional custom tags in case Apply Tags attribute is True|  No |

## Attributes Auto Mapping

### **Auto mapping from attributes to TF Variables**

Attributes that end with the postfix "_tfvar" will be automatically mapped to TF variables with the same name as the CloudShell attribute but without the postfix. <br>
> Example: The value of a CloudShell attribute called "DB_Name_tfvar" will be automatically assigned to a TF variable called "DB_Name".  

### **Auto mapping from TF Outputs to CloudShell attributes**

Attributes that end with the postfix "_tfout" will be automatically updated with the value of TF Outputs that has the same name but without the postfix.  <br>
> Example: The value of a TF output "DB_Hostname" will be automatically set on an attribute with the name "DB_Hostname_tfout".

## Config Object (cloudshell-iac-terraform)
The cloudshell-iac-terraform python package provides a configuration mechanism enabling you to set the behavior of the shell programmatically.
The config object is 'TerraformShellConfig' and it has the following parameters:

|Attribute Name|Data Type|Default Value|Description|
|:---|:---|:---|:---|
| write_sandbox_messages | bool  | False | When set to True will write info and error messages to the sandbox output |
| update_live_status | bool | False | When set to True will update the livestatus icon for the CloudShell Service using the cloudshell-iac-terraform python package |
| inputs_map | Dict | None | Defines a map between attribute names to TF variables. The value of the CloudShell attributes will be mapped to the TF variable |
| outputs_map | Dict | None | Defines a map between TF outputs to CloudShell attributes. TF outputs will be saved as values on the mapped CloudShell attributes |

The "Generic Terraform Service" contains an example of how to use the config object.

## Commands (generic_terraform_service)
|Command|Description|
|:-----|:-----|
|Execute Terraform| Takes care of the full deployment flow: Init, Plan and Apply.
|Destroy Terraform|Destroys the Terraform deployment previously done for this module.|

## Remote Backends (Remote Terraform State File)

Remote backend provider shells are used to apply remote backend functionality. If the "Remote State Provider" 
attribute is set with a name of a Remote Backend resource then the Terraform Shell will use this resource to get the
information needed in order to inject the required configuration to set the TF module to use a remote backend. 

It is strongly recommended to use this feature for security reasons.
Terraform creates a state file called tfstate and it can contain sensitive data in plain text. When using a remote backend the tfstate file will be stored in remote storage and access to this storage should be controlled to prevent exposing sensitive data.

### Azure Remote Provider Shell (backends\azure_tf_backend)

The Azure Remote Provider shell is used in order to enable CloudShell access to Azure storage, to then be used to store the remote state file.</br>
One must create a resource and fill in the attributes - then specify that resource name as the Remote State Provider.
Only one type of authentication is allowed, either by Access Key or using the Cloud Provider authentication keys. If both options are specified it will throw an error, so please supply only 1 option.

|Attribute|Type|Description|
|:-----|:-----|:-----|
Storage Account Name|String| The name of the Storage Account to be used |
Container Name|String| The name of the Container to be used |
Access Key|String| Access Key of the container|
Cloud Provider|String| Cloud Provider resource name that holds the authentication keys|
Resource Group|String| The resource group of the Storage Account|

### AWS Remote Provider Shell (backends\aws_tf_backend)
Coming soon

\* Additional Remote Backend Providers are coming soon

## Additional Notes

* In order to avoid sensitive data showing up in the logs, it's recommended to use Terraform version 0.14.0 or higher and set "sensitive = true" for all sensitive inputs and outputs.
* The cloudshell-iac-terraform python package will create 2 log files. The first log file is the standard logging file used by all CloudShell shells. The second log file will contain the raw output from Terraform commands like "terraform plan" for example. The name of this log will start with "TF_EXEC_LOG_".
* Unmapped sensitive outputs will be saved in an encrypted attribute ("password" type attribute) called "Terraform Sensitive Outputs" in case this attribute exists in shell-definition.yaml. Or ignored if the "Terraform Sensitive Outputs" doesn't exist.
* When using the auto mapping feature with sensitive outputs/inputs it's the responsibility of the Shell developer to use attributes of type "password" to avoid exposing sensitive data. 
* All the shell commands are executed on an Execution Server using python’s “Sub Process” package. All the commands are executed with "shell=False" for increased security to avoid exposing sensitive data. Due to "shell" being set to False, executions history will not be available in the Execution Server. 

## Contributing

All your contributions are welcomed and encouraged. We've compiled detailed information about contributing below:

* [Contributing](contributing.md)


## License
[Apache License 2.0](https://github.com/QualiSystemslab/CloudShell-Terraform-Shell/blob/master/LICENSE)
