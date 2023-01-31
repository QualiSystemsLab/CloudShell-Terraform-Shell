import os
import tempfile
from typing import Dict, List
from zipfile import ZipFile
import requests


class GitlabApiHttpError(Exception):
    pass


class GitlabApiHandler:
    def __init__(self, host: str, token: str = None, is_https=True):
        self.protocol = "https" if is_https else "http"
        self.host = host
        self.token = token
        self.base_url = f"{self.protocol}://{self.host}/api/v4"
        self.session = requests.Session()
        if self.token:
            self._add_auth_header()

    def _add_auth_header(self):
        self.session.headers.update({"PRIVATE-TOKEN": self.token})

    @staticmethod
    def _validate_response(response: requests.Response):
        if not response.ok:
            raise GitlabApiHttpError(f"Gitlab API Request Error. Status: {response.status_code}. Reason: {response.reason}")

    def get_project_data(self, project_name: str) -> dict:
        url = f"{self.base_url}/projects"
        with self.session as session:
            response = session.get(url=url, params={"search": project_name})
            self._validate_response(response)
            projects_list = response.json()
        if not projects_list:
            raise ValueError(f"No Project found with name '{project_name}'")
        return projects_list[0]

    def get_project_id_from_name(self, project_name: str) -> int:
        project_data = self.get_project_data(project_name)
        return project_data["id"]

    def get_project_directory_info(self, project_id: int, path: str, branch: str = "main") -> List[Dict]:
        """
        get a list of data on files inside directory
        list of dicts. ex: {id, name, type, path, mode}
        """
        url = f"{self.base_url}/projects/{project_id}/repository/tree"
        with self.session as session:
            response = session.get(url=url, params={"path": path, "ref": branch})
            self._validate_response(response)
            directory_info = response.json()
        if not directory_info:
            raise ValueError(f"No data found at repo path '{path}' for branch '{branch}'")
        return directory_info

    def get_directory_zip_bytes(self, project_id: int, path="", sha="") -> bytes:
        """
        nested path does not have to be url encoded
        "parent-dir/rds" is fine

        sha can be a branch or commit id - resolve to default branch
        https://docs.gitlab.com/ee/api/repositories.html#get-file-archive

        empty path resolves to entire project directory
        """
        url = f"{self.base_url}/projects/{project_id}/repository/archive.zip"
        params = {}
        if path:
            params["path"] = path
        if sha:
            params["sha"] = sha
        with self.session as session:
            response = session.get(url=url, params=params)
            self._validate_response(response)
            archive_bytes = response.content
        if not archive_bytes:
            raise ValueError(f"No archive data found. Project ID: {project_id}. Path: '{path}'. SHA: '{sha}'")
        return archive_bytes

    def download_zip(self, project_id: int, path: str, output_file_path: str, sha: str):
        """
        get bytes in response and dump to file
        nested path slashes do not have to be url encoded. "parent-dir/rds" is okay
        Output file has structure <output_file_path>.zip/<gitlab-generated-name>/git-parent-folder/folder2/file.txt
        """
        binary_data = self.get_directory_zip_bytes(project_id, path, sha)
        with open(output_file_path, "wb+") as file:
            file.write(binary_data)

    def download_archive_to_temp_dir(self, project_id: int, path: str, sha: str, zip_name="repo.zip", repo_dir_name="REPO"):
        binary_data = self.get_directory_zip_bytes(project_id, path, sha)
        working_dir = self._prepare_working_dir(repo_zip_file_name=zip_name,
                                                path_in_repo=path,
                                                zip_bytes=binary_data,
                                                repo_dir_name=repo_dir_name)
        return working_dir

    @staticmethod
    def _prepare_working_dir(repo_zip_file_name: str, path_in_repo: str, zip_bytes: bytes, repo_dir_name: str):
        """
        write zip bytes to temp directory
        this method will NOT delete the temp directory, whoever instantiates should clean up
        """
        repo_temp_dir = tempfile.mkdtemp()
        repo_zip_path = os.path.join(repo_temp_dir, repo_zip_file_name)

        # write zip to temp dir
        with open(repo_zip_path, 'wb+') as file:
            file.write(zip_bytes)

        # extract zip
        with ZipFile(repo_zip_path, 'r') as zip_file:
            zip_file.extractall(repo_temp_dir)

        # there will be one folder in zip, and another folder inside with name of repo path
        first_folder_in_zip = ZipFile(repo_zip_path, 'r').namelist()[0][:-1]
        first_folder_path = os.path.join(repo_temp_dir, first_folder_in_zip)
        working_dir_path = os.path.join(repo_temp_dir, repo_dir_name)
        os.rename(first_folder_path, working_dir_path)
        # working_dir = os.path.join(repo_temp_dir, repo_dir_name)
        for path_dir in path_in_repo.split("/"):
            working_dir_path = os.path.join(working_dir_path, path_dir)
        return working_dir_path


if __name__ == "__main__":
    api = GitlabApiHandler(host="192.168.85.26",
                           token="glpat-Kx6s8n2maL34CMc-AZ6s",
                           is_https=False)
    res = api.download_archive_to_temp_dir(project_id=2,
                                         path="parent-dir/hello-world",
                                         sha="test-branch")
    pass
