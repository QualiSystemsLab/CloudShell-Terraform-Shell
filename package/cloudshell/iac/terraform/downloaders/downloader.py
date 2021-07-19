from cloudshell.iac.terraform.downloaders.github_downloader import GitHubScriptDownloader
from cloudshell.iac.terraform.downloaders.tf_exec_downloader import TfExecDownloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject


class Downloader(object):
    def __init__(self, shell_helper: ShellHelperObject):
        self._shell_helper = shell_helper

    def download_terraform_module(self) -> str:
        url = self._shell_helper.tf_service.github_terraform_module_url

        token = ""
        if hasattr(self._shell_helper.tf_service, 'github_token'):
            token = self._shell_helper.api.DecryptPassword(self._shell_helper.tf_service.github_token).Value
        branch = ""
        if hasattr(self._shell_helper.tf_service, 'branch'):
            branch = self._shell_helper.tf_service.branch

        self._shell_helper.sandbox_messages.write_message("downloading Terraform module from repository...")
        self._shell_helper.logger.info("Downloading Terraform Repo from Github")

        downloader = GitHubScriptDownloader(self._shell_helper.logger)
        return downloader.download_repo(url, token, branch)

    def download_terraform_executable(self, tf_workingdir: str) -> None:
        try:
            self._shell_helper.logger.info("Downloading Terraform executable")
            self._shell_helper.sandbox_messages.write_message("downloading Terraform executable...")

            TfExecDownloader.download_terraform_executable(tf_workingdir,
                                                           self._shell_helper.tf_service.terraform_version)

        except Exception as e:
            self._shell_helper.logger.error(f"Failed downloading Terraform Repo from Github {str(e)}")
            raise
