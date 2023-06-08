import unittest

from cloudshell.iac.terraform.downloaders.gitlab_downloader import get_query_param_val


class TestQueryParamSearch(unittest.TestCase):
    QUERY_PARAMS = [["path", "parentdir/rds"], ["sha", "abcdefg"]]

    def test_param_search(self):
        path = get_query_param_val("path", self.QUERY_PARAMS)
        sha = get_query_param_val("sha", self.QUERY_PARAMS)
        self.assertEqual(path, "parentdir/rds")
        self.assertEqual(sha, "abcdefg")

    def test_not_found(self):
        ref = get_query_param_val("ref", self.QUERY_PARAMS)
        self.assertEqual(ref, "")
