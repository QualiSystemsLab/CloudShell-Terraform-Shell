import logging
from typing import Type

from cloudshell.cp.terraform.models.base_deployment_app import \
    TerraformDeploymentAppAttributeNames
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.iac.terraform.downloaders.base_git_downloader import \
    GitScriptDownloaderBase
from cloudshell.iac.terraform.downloaders.github_downloader import \
    GitHubScriptDownloader
from cloudshell.iac.terraform.downloaders.gitlab_downloader import \
    GitLabScriptDownloader
from cloudshell.iac.terraform.downloaders.tf_exec_downloader import TfExecDownloader


class CPDownloader(object):
    def __init__(self,
                 resource_config: TerraformResourceConfig,
                 logger: logging.Logger):
        self._resource_config = resource_config
        self._logger = logger

    def download_terraform_module(self, deploy_app: VMFromTerraformGit) -> str:
        url = deploy_app.git_terraform_url or self._resource_config.git_terraform_url
        if not url:
            raise \
                ValueError(f"Must populate attribute '"
                           f"{TerraformDeploymentAppAttributeNames.git_terraform_url}'")

        token = deploy_app.git_token or self._resource_config.git_token
        branch = deploy_app.branch or self._resource_config.branch

        # get downloader mapped to git provider
        provider = self._resource_config.git_provider.value()
        downloader = self._downloader_factory(provider, logger=self._logger)

        # download repo and return working dir
        self._logger.info(f"Downloading Terraform Repo from '{provider}'")
        self._logger.info(f"Download URL: '{url}'")
        return downloader.download_repo(url, token, branch)

    def download_terraform_executable(self, tf_workingdir: str) -> None:
        try:
            self._logger.info("Downloading Terraform executable")

            TfExecDownloader.download_terraform_executable(
                tf_workingdir,
                self._resource_config.terraform_version,
            )
        except Exception as e:
            self._logger.error(f"Failed downloading Terraform Repo from Github {str(e)}")
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
