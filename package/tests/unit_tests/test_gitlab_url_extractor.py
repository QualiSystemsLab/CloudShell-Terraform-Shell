import unittest
from cloudshell.iac.terraform.downloaders import gitlab_downloader


class TestGitlabUrlExtractor(unittest.TestCase):
    """
    raw url as seen in browser has format
    http://<domain>/<user>/<projectname>/-/tree/<branch>/<folderpath>

    api style url:
    http://<domain>/api/v4/projects/<project_id>/repository/archive.zip?path=<path>=<branch>
    """
    BROWSER_URL = "http://192.168.85.26/quali_natti/terraformstuff/-/tree/test-branch/parent-dir/hello-world"
    API_URL = "http://192.168.85.26/api/v4/projects/2/repository/archive.zip?path=parent%2Ddir%2Fhello%2Dworld&sha=test%2Dbranch"

    def test_browser_url(self):
        url_data = gitlab_downloader.extract_data_from_browser_url(self.BROWSER_URL)
        assert url_data

    def test_api_url(self):
        url_data = gitlab_downloader.extract_data_from_api_url(self.API_URL)
        assert url_data

    def test_api_url_validate(self):
        assert gitlab_downloader.is_gitlab_api_url(self.API_URL)
        assert not gitlab_downloader.is_gitlab_api_url(self.BROWSER_URL)

    def test_browser_vs_api_url_data(self):
        browser_data = gitlab_downloader.extract_data_from_browser_url(self.BROWSER_URL)
        api_data = gitlab_downloader.extract_data_from_api_url(self.API_URL)
        self.assertEqual(browser_data.domain, api_data.domain)
        self.assertEqual(browser_data.path, api_data.path)
        self.assertEqual(browser_data.sha, api_data.sha)

    def test_raises(self):
        url_arg = "http://www.google.com"
        self.assertRaises(ValueError, gitlab_downloader.extract_data_from_api_url, url_arg)
        self.assertRaises(ValueError, gitlab_downloader.extract_data_from_browser_url, url_arg)
