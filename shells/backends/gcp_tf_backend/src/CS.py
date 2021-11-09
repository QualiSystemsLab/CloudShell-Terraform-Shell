from pprint import pprint
from googleapiclient import discovery
# from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account
import os
import json

class GCPService:
    def __init__(self, project):
        self.project = project #cloudshell-gcp
        self.client = None
        # pass

    def _get_client(self):
        if self.client:
            return self.client

        self.client = discovery.build('compute', 'v1')
        return self.client

    def can_connect(self):
        ret = False

        client = self._get_client()

        response = client.healthChecks().list(project=self.project).execute()
        print(response)
        # return response
        return len(response) > 0





def _get_service(project, key, email):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump({ "type": "service_account", "project_id": project, "private_key": key, "client_email": email,"auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token" }, f, ensure_ascii=False, indent=4)

    with open("data.json", "r") as d:
        print(d.read())
        
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data.json" 

    gcp_service = GCPService(project=project)
    return gcp_service


project="alexs-project-239406"
key="testn"
email="test"
gcp_service = _get_service(project, key, email)
if not gcp_service.can_connect():
    raise ValueError('Could not connect: Check credentials')

os.remove("data.json")

# def get_inventory(self, context):
#     """
#     Discovers the resource structure and attributes.
#     :param AutoLoadCommandContext context: the context the command runs on
#     :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
#     :rtype: AutoLoadDetails
#     """

#     with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
#         with CloudShellSessionContext(context) as cloudshell_session:
#             self._log(logger, 'get_inventory_context_json', context)

#             cloud_provider_resource = GoogleCloudProvider.create_from_context(context)

#             gcp_service = self._get_service(cloud_provider_resource, logger)

#             if not gcp_service.can_connect():
#                 raise ValueError('Could not connect: Check credentials')

#     return cloud_provider_resource.create_autoload_details()