import logging
from typing import Type

from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.downloaders.tf_exec_downloader import TfExecDownloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.downloaders.base_git_downloader import GitScriptDownloaderBase
from cloudshell.iac.terraform.downloaders.github_downloader import GitHubScriptDownloader
from cloudshell.iac.terraform.downloaders.gitlab_downloader import GitLabScriptDownloader


class Downloader(object):
    def __init__(self, shell_helper: ShellHelperObject):
        self._shell_helper = shell_helper

    def download_terraform_module(self) -> str:
        url = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.GIT_TERRAFORM_MODULE_URL)
        if not url:
            raise ValueError(f"Must populate attribute '{ATTRIBUTE_NAMES.GIT_TERRAFORM_MODULE_URL}'")

        token_enc = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.GIT_TOKEN)
        token = self._shell_helper.api.DecryptPassword(token_enc).Value
        branch = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.BRANCH)

        # get downloader mapped to git provider
        provider = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.GIT_PROVIDER)
        downloader = self._downloader_factory(provider, logger=self._shell_helper.logger)

        # download repo and return working dir
        self._shell_helper.sandbox_messages.write_message("downloading Terraform module from repository...")
        self._shell_helper.logger.info(f"Downloading Terraform Repo from '{provider}'")
        self._shell_helper.logger.info(f"Download URL: '{url}'")
        return downloader.download_repo(url, token, branch)

    def download_terraform_executable(self, tf_workingdir: str) -> None:
        try:
            self._shell_helper.logger.info("Downloading Terraform executable")
            self._shell_helper.sandbox_messages.write_message("downloading Terraform executable...")

            TfExecDownloader.download_terraform_executable(
                tf_workingdir,
                self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.TERRAFORM_VERSION)
            )
        except Exception as e:
            self._shell_helper.logger.error(f"Failed downloading Terraform Repo from Github {str(e)}")
            raise

    def _get_downloader_class(self, git_provider: str) -> Type[GitScriptDownloaderBase]:
        """ extend this dictionary with additional git provider downloaders """
        git_downloader_map = {
            "github": GitHubScriptDownloader,
            "gitlab": GitLabScriptDownloader
        }
        if git_provider.lower() not in git_downloader_map:
            raise NotImplementedError(f"Git Provider '{git_provider}' not supported")
        return git_downloader_map[git_provider.lower()]

    def _downloader_factory(self, git_provider: str, logger: logging.Logger) -> GitScriptDownloaderBase:
        downloader_class = self._get_downloader_class(git_provider)
        return downloader_class(logger)
