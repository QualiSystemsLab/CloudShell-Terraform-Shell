import shutil
import unittest
from cloudshell.iac.terraform.downloaders.gitlab_downloader import GitLabScriptDownloader
from tests.integration_tests.helper_objects.stdout_logger import get_test_logger
from tests.integration_tests.helper_objects.env_vars import GitLabEnvVars
import os


class TestGitlabDownloader(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = get_test_logger()
        self.gitlab_vars = GitLabEnvVars()
        self.downloader = GitLabScriptDownloader(self.logger)
        self.working_dir = None

    def test_api_url_download(self):
        working_dir = self.downloader.download_repo(url=self.gitlab_vars.api_url,
                                                    token=self.gitlab_vars.token,
                                                    branch=self.gitlab_vars.branch)
        self.working_dir = working_dir
        assert working_dir

    def test_browser_url_download(self):
        working_dir = self.downloader.download_repo(url=self.gitlab_vars.natural_url,
                                                    token=self.gitlab_vars.token,
                                                    branch=self.gitlab_vars.branch)
        self.working_dir = working_dir
        assert working_dir

    def tearDown(self) -> None:
        shutil.rmtree(self.working_dir, ignore_errors=True)
        print(f"is dir: {os.path.isdir(self.working_dir)}")
