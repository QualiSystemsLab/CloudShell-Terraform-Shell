import unittest
from cloudshell.iac.terraform.downloaders import gitlab_downloader


class TestGitlabUrlExtractor(unittest.TestCase):
    RAW_URL = "http://192.168.85.26/quali_natti/terraformstuff/-/tree/test-branch/rds"
    API_URL = "http://192.168.85.26/api/v4/projects/2/repository/archive.zip?path=rds"

    def test_raw_url(self):
        url_data = gitlab_downloader.extract_data_from_raw_url(self.RAW_URL)
        assert url_data

    def test_api_url_extract(self):
        url_data = gitlab_downloader.extract_data_from_api_url(self.API_URL)
        assert url_data

    def test_api_validate(self):
        assert gitlab_downloader.is_gitlab_api_url(self.API_URL)
        assert not gitlab_downloader.is_gitlab_api_url(self.RAW_URL)

    def test_raises(self):
        url_arg = ""
        self.assertRaises(ValueError, gitlab_downloader.extract_data_from_api_url, url_arg)
        self.assertRaises(ValueError, gitlab_downloader.extract_data_from_raw_url, url_arg)
