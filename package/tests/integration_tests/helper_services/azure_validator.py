import os
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient


class AzureValidator(object):
    def __init__(self):
        self._subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
        self._client_id = os.environ['AZURE_APPLICATION_ID']
        self._secret = os.environ['AZURE_APPLICATION_KEY_DEC']
        self._tenant = os.environ['AZURE_TENANT_ID']
        self._credentials = ServicePrincipalCredentials(
            client_id=self._client_id,
            secret=self._secret,
            tenant=self._tenant
        )
        self._client = ResourceManagementClient(self._credentials, self._subscription_id)

        for item in self._client.resource_groups.list():
            print(item)