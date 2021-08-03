# CloudShell-Terraform-Shell
Purpose: allow execution of Terraform deployment from CloudShell. Multiple “Terraform Service” services can be added to a Blueprint or Sandbox, and these can be executed from CloudShell Portal UI by the user that is reserving the Blueprint.

Additional workflow recommendation: it is very easy to customize Blueprint setup script that will run the “Deploy Terraform” command on the service, and a similar teardown script that will run the “Destroy Terraform” command – this way the Terraform Module lifecycle is connected to the Sandbox lifecycle.

## Content
* (1) cloudshell-iac-terraform - Python package
* (2) generic_terraform_service - Main Shell
  * Used in a generic fashion or used to build an extension for a specific purpose (e.g. MsSql)
* (3) backends\azure_tf_backend - Azure Remote Provider Shell

## Shell Usage Instructions
 
1. Import Shell(/s) to CloudShell “Shells” screen.
2. Add Terraform Service to Blueprint/Sandbox.
3. Configure the different attributes to match the requirement of the deployment.</br>
   \* Please see below the documentation per attribute.

## Config Object (cloudshell-iac-terraform)
The shell proivdes a configuration mechanism enabling you to set the behavior of the shell
The object is 'TerraformShellConfig' and holds the following parameters:

|Attribute Name|Data Type|Default Value|Description|
|:---|:---|:---|:---|
| write_sandbox_messages | bool  | False | |
| update_live_status | bool | False | |
| inputs_map | Dict | None | |
| outputs_map | Dict | None | |

## Service Attributes (generic_terraform_service)
|Attribute Name|Data Type|Description|Mandatory?|
|:---|:---|:---|:---|
|Github Terraform Module URL|String|path to target module. Can be provided in three formats: <br/> 1)https://github.com/ACCOUNT/REPO/tree/BRANCH/PATH_TO_FOLDER <br/> 2)https://github.com/ACCOUNT/REPO/blob/BRANCH/PATH_TO_FOLDER/FILENAME.tf<br/> 3)https://raw.githubusercontent.com/ACCOUNT/REPO/BRANCH/PATH_TO_FOLDER/FILENAME.tf  | Yes |
|Terraform Version|String|The version of terraform.exe that will be downloaded and used (If not specified latest version will be used)|  No |
|Github Token|String| Github developer token to be used in order to download TF module|  Yes |
|Cloud Provider|String| Reference to the CloudProvider resource that shall be used to create authentication| Yes |
|Branch|String| In case specified will override the branch in the Github Terraform Module URL |  No |
|Terraform Outputs|String| Used by the system to place the non-sensitive execution outputs|  No |
|Terraform Sensitive Outputs|String|Used by the system to place the sensitive execution outputs|  No |
|Terraform Inputs|String|Comma separated values to specify TF inputs (e.g. varname1=varvalue1,varname2=varvalue2...)| * |
|Remote State Provider|String|Reference a Remote State provider resource to enable remote state file</br> If not specified the statefile will be kept locally and a temp directory will remain present after execution and only removed after successful destroy|  No |
|Custom Tags|String|Comma separated name=value list to be used in case Auto Tagging is enabled|  No |
|Apply Tags|Boolean|Specify whether TF resources will be auto-tagged|  N/A|
\* if required by the tf module

## Commands (generic_terraform_service)
|Command|Description|
|:-----|:-----|
|Execute Terraform module| Takes care of the full deployment cycle:<br/>INIT<br/>PLAN<br/>APPLY|
|Destroy Terraform module|Destroys the Terraform deployment previously done for this module.|

## Azure Remote Provider Shell (backends\azure_tf_backend)

The Azure Remote Provider shell is used in order to enable Cloudshell access to Azure storage to be used in order to store the remote statefile.</br>
One must create a resource and fill in the attributes - then specify that resource name as the Remote State Provider.
Only one type of authentication is allowed either by Access Key or using the Cloud Provider authentication keys.

|Attribute|Type|Description|
|:-----|:-----|:-----|
Storage Account Name|String| The name of the Storage Account to be used |
Container Name|String| The name of the Container to be used |
Access Key|String| Access Key of the container|
Cloud Provider|String| Cloud Provider resource name that holds the authentication keys|
Resource Group|String| The resource group of the Storage Account|

## xxx Remote Provider Shell (backends\xxx_tf_backend)
\* Additional Remote Providers soon to come (TBD)

## Additional Notes

### Discretion

* Sensitive output will encrypted and appear in the UI as bullet dots
* Logs will not include sensitive data
* Executions history will not be accessible via Execution Server access

### Logging




- All of the shell commands are executed using python’s “Sub Process” package on the Execution Server that is running the Shell command.
- The Terraform Shell can run locally on the execution server – it requires that there’s access from the execution server to the path where Terraform.exe is located and to the path where the Terraform module is located.
- It is also possible to put the Terraform module on a shared network location (example: \\my-storage-server\terraform\module_name) and grant permission to that storage server to the System account (Host_Name$) of the execution server
