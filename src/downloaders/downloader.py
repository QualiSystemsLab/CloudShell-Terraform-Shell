from downloaders.github_downloader import GitHubScriptDownloader
from downloaders.tf_exec_downloader import TfExecDownloader
from driver_helper_obj import DriverHelperObject


class Downloader(object):
    def __init__(self, driver_helper_obj: DriverHelperObject):
        self._driver_helper_obj = driver_helper_obj

    def download_terraform_module(self) -> str:
        url = self._driver_helper_obj.tf_service.github_terraform_module_url
        token = self._driver_helper_obj.api.DecryptPassword(self._driver_helper_obj.tf_service.github_token).Value

        self._driver_helper_obj.api.WriteMessageToReservationOutput(self._driver_helper_obj.res_id,
                                                                    "Downloading Terraform from repository...")
        self._driver_helper_obj.logger.info("Downloading Terraform Repo from Github")

        downloader = GitHubScriptDownloader(self._driver_helper_obj.logger)
        return downloader.download_repo(url, token)

    def download_terraform_executable(self, tf_workingdir: str) -> None:
        try:
            self._driver_helper_obj.logger.info("Downloading Terraform Executable")
            self._driver_helper_obj.api.WriteMessageToReservationOutput(self._driver_helper_obj.res_id,
                                                                        "Downloading Terraform Executable...")

            TfExecDownloader.download_terraform_executable(tf_workingdir,
                                                           self._driver_helper_obj.tf_service.terraform_version)

        except Exception as e:
            self._driver_helper_obj.logger.error(f"Failed downloading Terraform Repo from Github {str(e)}")
            raise