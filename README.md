# Terraform-Service-2G
Purpose: allow execution of Terraform deployment from CloudShell. Multiple “Terraform Service” services can be added to a Blueprint or Sandbox, and these can be executed from CloudShell Portal UI by the user that is reserving the Blueprint.

Additional workflow recommendation: it is very easy to customize Blueprint setup script that will run the “Deploy Terraform” command on the service, and a similar teardown script that will run the “Destroy Terraform” command – this way the Terraform Module lifecycle is connected to the Sandbox lifecycle.

## Shell Usage Instructions
1. Import Shell to CloudShell “Shells” screen.
2. Add Terraform Service to Blueprint/Sandbox.
3. In “Terraform Executable” – put path to folder containing “Terraform.exe”
4. In “Terraform Module Path” – put path to folder containing Terraform module that the customer wants to deploy.

## 2G Service Attributes
|Attribute Name|Data Type|Description|
|:---|:---|:---|
|Terraform Module Path|String|path to target module. Target directory will be changed to here before running terraform commands.|
|Terraform Executable|String|path to folder with terraform.exe|

## Commands
|Command|Description|
|:-----|:-----|
|Run Terraform|Deploys the Terraform module in the folder put in “Terraform Module Path”|
|Destroy Terraform|Destroys the Terraform deployment previously done for this module.|
|Plan Terraform|Returns the planned changes for “Deploy Terraform” without Deploying anything.|
|Show Terraform State|Returns the content of the “terraform.tfstate” file that shows the currently deployed resources from this module.|

## Additional Notes
- All of the shell commands are executed using python’s “Sub Process” package on the Execution Server that is running the Shell command.
- The Terraform Shell can run locally on the execution server – it requires that there’s access from the execution server to the path where Terraform.exe is located and to the path where the Terraform module is located.
- It is also possible to put the Terraform module on a shared network location (example: \\my-storage-server\terraform\module_name) and grant permission to that storage server to the System account (Host_Name$) of the execution server
