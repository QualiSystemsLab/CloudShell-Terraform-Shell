#!/usr/bin/env python
from cloudshell.shell.core.driver_context import ResourceCommandContext

"""
Tests for `GcpTfBackendDriver`
"""

import unittest

from driver import GcpTfBackendDriver


class TestGcpTfBackendDriver(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_something(self):
        pass


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())

if __name__ == "__main__":
    from unittest import mock

    from cloudshell.shell.core.driver_context import CancellationContext

    shell_name = "Gcp Tf Backend"
    # model_name = ""

    from cloudshell.api.cloudshell_api import CloudShellAPISession

    host = "localhost"
    username = "admin"
    password = "admin"
    domain = "Global"

    pythonApi = CloudShellAPISession(host, username, password, domain)
    print(pythonApi)

    authToken = (
        pythonApi.authentication.xmlrpc_token
    )  # Use "pythonApi.token_id" with cloudshell-automation-api version 2020.1.0.178672 and below
    print(authToken)
    # connectivity.admin_auth_token = authToken

    cancellation_context = mock.create_autospec(CancellationContext)
    context = mock.create_autospec(ResourceCommandContext)
    # context.resource = mock.MagicMock()
    context.resource = mock.MagicMock()
    # context.reservation = mock.MagicMock()
    context.reservation = mock.MagicMock()
    # context.connectivity = mock.MagicMock()
    context.connectivity = mock.MagicMock()
    context.connectivity.serverAddress = host
    context.connectivity.server_address = host
    # context.reservation.reservation_id = "c13a6d18-07fe-4651-89c5-f3ee70220d0b"
    context.resource.address = host
    context.resource.connectivity.server_address = host
    context.resource.name = "myname"
    context.connectivity.admin_auth_token = authToken
    context.resource.attributes = dict()
    context.resource.attributes[f"{shell_name}.Project"] = "alexs-project-239406"
    context.resource.attributes[f"{shell_name}.Cloud Provider"] = "test-GCP"
    # context.resource.attributes["{}.Client Email".format(shell_name)] = 'AWJdt6fWWmRupkI9qOUcbzf+cB/+BSk3k1D7ELiR6HTT+bcepfvD/zWVcnYU3GkdeqO/Ridyjfn0DSZqERycuA=='
    # "oleksandr-r@alexs-project-239406.iam.gserviceaccount.com"
    # context.resource.attributes["{}.Password".format(shell_name)] = password
    # context.resource.attributes["{}.SNMP Read Community".format(shell_name)] = "<READ_COMMUNITY_STRING>"
    # 'C:\\Users\\CSadmin123456\\CS\\tf-gcp\\prod.json'
    driver = GcpTfBackendDriver()
    # print driver.run_custom_command(context, custom_command="sh run", cancellation_context=cancellation_context)
    driver.initialize(context)
    result = driver.get_inventory(context)
    # result = driver.example_command(context)
    print(result)
    print("done")
