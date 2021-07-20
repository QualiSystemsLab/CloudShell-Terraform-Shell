from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.downloaders.github_downloader import GitHubScriptDownloader
from cloudshell.iac.terraform.downloaders.tf_exec_downloader import TfExecDownloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler


class Downloader(object):
    def __init__(self, shell_helper: ShellHelperObject):
        self._shell_helper = shell_helper

    def download_terraform_module(self) -> str:
        url = self._shell_helper.tf_service.github_terraform_module_url

        token = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.GITHUB_TOKEN)
        branch = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.BRANCH)

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
