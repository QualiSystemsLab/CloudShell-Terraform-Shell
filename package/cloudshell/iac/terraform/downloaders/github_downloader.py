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

GitHubFileData = collections.namedtuple(
    'GitHubFileData', 'account_id repo_id branch_id path api_zip_dl_url api_tf_dl_url'
)
REPO_FILE_NAME = "repo.zip"


class GitHubScriptDownloader(object):
    GITHUB_REPO_PATTERN = "^https://.+?/(?P<account_id>.+?)/(?P<repo_id>.+?)/(?:blob|tree)/(?P<branch_id>.+?)/(?P<path>.*?)$"

    def __init__(self, logger: Logger):
        self.logger = logger

    @retry((HTTPError, URLError), delay=1, backoff=2, tries=5)
    def download_repo(self, url: str, token: str) -> str:
        headers = {'Authorization': f'token {token}'}
        self._validate_github_url(url)
        url_data = self._extract_data_from_url(url)
        try:
            # Downloading the path provided to check if it exists
            tf_response = requests.get(url_data.api_tf_dl_url, headers=headers)
            tf_response_json = json.loads(tf_response.text)

            if tf_response.status_code == 200:
                path_in_repo = url_data.path
                repo_response = requests.get(url_data.api_zip_dl_url, headers=headers)
                # Downloading the Repo and checking it get downloaded
                if repo_response.status_code == 200:

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
                    os.chdir(repo_temp_dir)
                    os.rename(commit_folder_in_zip, "REPO")
                    return os.path.join(repo_temp_dir, "REPO", path_in_repo)
                else:
                    raise Exception(f'Error Downloading/Extracting - Download code for repo '
                                    f'{repo_response.status_code}')
            else:
                raise Exception(f'Error Downloading/Extracting - Download code for path '
                                f'{tf_response.status_code}')
        except Exception as e:
            self.logger.error(f'There was an error downloading and extracting the repo. {str(e)}')
            raise

    def _extract_repo(self, source: str, destination: str) -> None:
        self.logger.info(f"Extracting {REPO_FILE_NAME}")
        ZipFile(source, 'r').extractall(destination)

    def _validate_github_url(self, url: str) -> None:
        matching = re.match(self.GITHUB_REPO_PATTERN, url)

        if not matching:
            self._raise_url_syntax_error()

    def _raise_url_syntax_error(self) -> None:
        raise ValueError("Provided GitHub URL is not in the correct format. "
                         "Expected format is the GitHub API syntax. "
                         "Example: 'https://github.com/:account_id/:repo/blob/:branch/:path'")

    def _extract_data_from_url(self, url: str):
        """
        :param str url:
        :rtype: GitHubFileData
        """
        matching = re.match(self.GITHUB_REPO_PATTERN, url)

        if matching:

            matched_groups = matching.groupdict()

            account_id = matched_groups['account_id']
            repo_id = matched_groups['repo_id']
            branch_id = matched_groups['branch_id']
            path = matched_groups['path']

            api_zip_dl_url = f'https://api.github.com/repos/{account_id}/{repo_id}/zipball/{branch_id}'
            # API to get metadata about file/dir
            api_tf_dl_url = f'https://api.github.com/repos/{account_id}/{repo_id}/contents/{path}?ref={branch_id}'

            # self.logger.info(msg=f'API Call will use the following address {api_zip_dl_url}')
            return GitHubFileData(account_id, repo_id, branch_id, path, api_zip_dl_url, api_tf_dl_url)
        else:
            self._raise_url_syntax_error()
