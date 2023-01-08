import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from retry import retry
from cloudshell.iac.terraform.downloaders.base_git_downloader import GitScriptDownloaderBase
from cloudshell.iac.terraform.services.gitlab_api_handler import GitlabApiHandler


@dataclass
class CommonGitLabUrlData:
    protocol: str
    domain: str
    path: str
    full_url: str


@dataclass
class GitLabNaturalUrlData(CommonGitLabUrlData):
    gitlab_user: str
    project_name: str
    branch: str


@dataclass
class GitLabApiUrlData(CommonGitLabUrlData):
    api_version: str
    project_id: int
    api_endpoint: str


def extract_data_from_natural_url(url):
    """
    Take api style url and extract data
    Sample Natural url: "http://192.168.85.26/quali_natti/terraformstuff/-/tree/test-branch/rds"
    """

    pattern = (r'^(?P<protocol>https?)://(?P<domain>[^/]+)/(?P<user>[^/]+)/(?P<project>[^/]+)/'
               r'(-/tree/(?P<branch>[^/]+))?(?P<path>/.*)?$')

    match = re.match(pattern, url)
    if not match:
        raise ValueError(f"No GitLab Natural URL match found for url '{url}'")

    groups = match.groupdict()
    return GitLabNaturalUrlData(protocol=groups['protocol'],
                                domain=groups['domain'],
                                gitlab_user=groups['user'],
                                project_name=groups['project'],
                                branch=groups['branch'],
                                path=groups['path'],
                                full_url=url)


def extract_data_from_api_url(url):
    """
    Take user style url and extract data
    Sample Api url: "http://192.168.85.26/api/v4/projects/2/repository/archive.zip?path=rds"
    """

    pattern = (r'^(?P<protocol>https?)://(?P<domain>[^/]+)(?P<api_version>/api/v\d+)?'
               r'(?P<api_endpoint>/projects/(?P<project_id>\d+)/repository/archive\.zip)(\?path=(?P<path>[^&]+))?$')

    match = re.match(pattern, url)
    if not match:
        raise ValueError(f"No GitLab API URL match found for url '{url}'")

    groups = match.groupdict()
    return GitLabApiUrlData(protocol=groups['protocol'],
                            domain=groups['domain'],
                            api_version=groups['api_version'],
                            project_id=groups['project_id'],
                            api_endpoint=groups['api_endpoint'],
                            path=groups['path'],
                            full_url=url)


def is_gitlab_api_url(url: str) -> bool:
    """
    check if is api endpoint
    Sample Api url: "http://192.168.85.26/api/v4/projects/2/repository/archive.zip?path=rds"
    """
    pattern = r'^(?P<protocol>https?)://(?P<domain>[^/]+)(?P<api_version>/api/v\d+)?(?P<api_endpoint>/[^\s]+)*/?$'
    match = re.match(pattern, url)
    if not match:
        return False

    groups = match.groupdict()
    api_version = groups['api_version']  # "/api/v4"

    if not api_version:
        return False

    return True


class GitLabScriptDownloader(GitScriptDownloaderBase):

    @retry((HTTPError, URLError), delay=1, backoff=2, tries=5)
    def download_repo(self, url: str, token: str, branch: str = "") -> str:
        is_api_url = is_gitlab_api_url(url)
        if is_api_url:
            url_data = extract_data_from_api_url(url)
        else:
            url_data = extract_data_from_natural_url(url)
        is_https = True if url_data.protocol == "https" else False
        api_handler = GitlabApiHandler(host=url_data.domain, token=token, is_https=is_https)
        project_id = url_data.project_id if is_api_url else api_handler.get_project_id_from_name(url_data.project_name)
        working_dir = api_handler.download_archive_to_temp_dir(project_id=project_id, path=url_data.path, sha=branch)
        self.logger.info(f"Temp Working Dir: {working_dir}")
        return working_dir
