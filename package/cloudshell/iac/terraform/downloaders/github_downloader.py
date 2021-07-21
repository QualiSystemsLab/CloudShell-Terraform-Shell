import collections
import json
import os
import re
from logging import Logger
from zipfile import ZipFile
import tempfile
import requests
from urllib.error import HTTPError, URLError

from retry import retry

from cloudshell.iac.terraform.constants import GITHUB_REPO_PATTERN

GitHubFileData = collections.namedtuple(
    'GitHubFileData', 'account_id repo_id branch_id path api_zip_dl_url api_tf_dl_url'
)
REPO_FILE_NAME = "repo.zip"


class GitHubScriptDownloader(object):

    def __init__(self, logger: Logger):
        self.logger = logger

    @retry((HTTPError, URLError), delay=1, backoff=2, tries=5)
    def download_repo(self, url: str, token: str, branch: str = "") -> str:
        headers = {'Authorization': f'token {token}'}
        self._validate_github_url(url)
        url_data = self._extract_data_from_url(url, branch)
        try:
            # Downloading the path provided to check if it exists
            tf_response = requests.get(url_data.api_tf_dl_url, headers=headers)
            tf_response_json = json.loads(tf_response.text)

            if tf_response.status_code == 200:
                path_in_repo = url_data.path
                repo_response = requests.get(url_data.api_zip_dl_url, headers=headers)
                # Downloading the Repo and checking it get downloaded
                if repo_response.status_code == 200:
                    working_dir = self._prepare_working_dir(path_in_repo, repo_response, tf_response_json, url_data)
                    return working_dir
                else:
                    raise Exception(f'Error Downloading/Extracting: Download code for repo={repo_response.status_code}')
            else:
                raise Exception(f'Error Downloading/Extracting - Download code for module url (Check Token and URL)'
                                f'{tf_response.status_code}')
        except Exception as e:
            self.logger.error(f'There was an error downloading and extracting the repo. {str(e)}')
            raise

    def _prepare_working_dir(self, path_in_repo, repo_response, tf_response_json, url_data):
        # Removing the file from the path as we are interested in the Folder that contains it
        if not isinstance(tf_response_json, list):
            path_in_repo = os.sep.join(url_data.path.split("/")[:-1])
        repo_temp_dir = tempfile.mkdtemp()
        self.logger.info(f"Temp repo dir = {repo_temp_dir}")
        repo_zip_path = os.path.join(repo_temp_dir, REPO_FILE_NAME)
        with open(os.path.join(repo_temp_dir, REPO_FILE_NAME), 'wb+') as file:
            file.write(repo_response.content)
        self._extract_repo(repo_zip_path, repo_temp_dir)
        commit_folder_in_zip = ZipFile(repo_zip_path, 'r').namelist()[0][:-1]
        os.rename(os.path.join(repo_temp_dir, commit_folder_in_zip), os.path.join(repo_temp_dir, "REPO"))
        working_dir = os.path.join(repo_temp_dir, "REPO")
        for path_in_repo_dir in path_in_repo.split("/"):
            working_dir = os.path.join(working_dir, path_in_repo_dir)
        self.logger.info(f"Working dir = {working_dir}")
        return working_dir

    def _extract_repo(self, source: str, destination: str) -> None:
        self.logger.info(f"Extracting {REPO_FILE_NAME}")
        ZipFile(source, 'r').extractall(destination)

    def _validate_github_url(self, url: str) -> None:
        matching = re.match(GITHUB_REPO_PATTERN, url)

        if not matching:
            self._raise_url_syntax_error()

    def _raise_url_syntax_error(self) -> None:
        raise ValueError("Provided GitHub URL is not in the correct format. "
                         "Expected format is the GitHub API syntax. "
                         "Example: 'https://github.com/:account_id/:repo/blob/:branch/:path' or "
                         "Example: 'https://raw.githubusercontent.com/:account_id/:repo/:branch/:path'")

    def _extract_data_from_url(self, url: str, branch_attr: str = ""):
        """
        :param str url:
        :rtype: GitHubFileData
        """
        matching = re.match(GITHUB_REPO_PATTERN, url)

        if matching:

            matched_groups = matching.groupdict()

            account_id = matched_groups['account_id']
            repo_id = matched_groups['repo_id']
            branch_id = matched_groups['branch_id']
            path = matched_groups['path']

            if branch_attr:
                branch_id = branch_attr

            api_zip_dl_url = f'https://api.github.com/repos/{account_id}/{repo_id}/zipball/{branch_id}'
            # API to get metadata about file/dir
            api_tf_dl_url = f'https://api.github.com/repos/{account_id}/{repo_id}/contents/{path}?ref={branch_id}'

            return GitHubFileData(account_id, repo_id, branch_id, path, api_zip_dl_url, api_tf_dl_url)
        else:
            self._raise_url_syntax_error()
