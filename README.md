# CloudShell-Terraform-Shell
Purpose: allow execution of Terraform deployment from CloudShell. Multiple “Terraform Service” services can be added to a Blueprint or Sandbox, and these can be executed from CloudShell Portal UI by the user that is reserving the Blueprint.

Additional workflow recommendation: it is very easy to customize Blueprint setup script that will run the “Deploy Terraform” command on the service, and a similar teardown script that will run the “Destroy Terraform” command – this way the Terraform Module lifecycle is connected to the Sandbox lifecycle.

## Shell Usage Instructions
1. Import Shell to CloudShell “Shells” screen.
2. Add Terraform Service to Blueprint/Sandbox.
3. Configure the different attributes to match the requirement of the deployment.
   *Please see below the documentation per attribute.

## Service Attributes
|Attribute Name|Data Type|Description|
|:---|:---|:---|
|Github Terraform Module URL|String|path to target module. Can be provided in three formats: <br/> 1)https://github.com/<ACCOUNT>/<REPO>/tree/<BRANCH>/<PATH_TO_FOLDER> <br/> 2)https://github.com/<ACCOUNT>/<REPO>/blob/<BRANCH>/<PATH_TO_FOLDER>/filename.tf<br/> 3)https://raw.githubusercontent.com/<ACCOUNT>/<REPO>/<BRANCH>/<PATH_TO_FOLDER>/filename.tf  |
|Terraform Version|String|The version of terraform.exe that will be downloaded and used (If not specified latest version will be used)|
|Github Token|String| Github developer token to be used in order to download TF module|
|Cloud Provider|String| Reference to the CloudProvider resource that shall be used to create authentication|
|Branch|String| In case specified will override the branch in the Github Terraform Module URL |
|Terraform Outputs|String| Used by the system to place the non-sensitive execution outputs|
|Terraform Sensitive Outputs|String|Used by the system to place the sensitive execution outputs|
|Terraform Inputs|String|Comma separated values to specify TF inputs (e.g. varname1=varvalue1,varname2=varvalue2...)|
|Remote State Provider|String|Reference a Remote State provider resource to enable remote state file|
|Custom Tags|String|Comma separated name=value list to be used in case Auto Tagging is enabled|
|Apply Tags|Boolean|Specify whether TF resources will be auto-tagged|

## Commands
|Command|Description|
|:-----|:-----|
|Execute Terraform module| Takes care of the full deployment cycle:<br/>INIT<br/>PLAN<br/>APPLY|
|Destroy Terraform module|Destroys the Terraform deployment previously done for this module.|

## Additional Notes
- All of the shell commands are executed using python’s “Sub Process” package on the Execution Server that is running the Shell command.
- The Terraform Shell can run locally on the execution server – it requires that there’s access from the execution server to the path where Terraform.exe is located and to the path where the Terraform module is located.
- It is also possible to put the Terraform module on a shared network location (example: \\my-storage-server\terraform\module_name) and grant permission to that storage server to the System account (Host_Name$) of the execution server
