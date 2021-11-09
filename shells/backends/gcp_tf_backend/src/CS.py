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
    # json_path="data.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data.json" 
    # with open('data.json', 'w', encoding='utf-8') as f:
    #     json.dump("C:\\Users\\CSadmin123456\\CS\\tf-gcp\\prod.json", f, ensure_ascii=False, indent=4)

    # project = "alexs-project-239406"
    # json_path = "C:\\Users\\CSadmin123456\\CS\\tf-gcp\\prod.json"

    gcp_service = GCPService(project=project)
    return gcp_service


project="alexs-project-239406"
key="-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCumSnK3R5sHAwo\nyoNvd0/jUCti5Gd/x4XPf6uAO6oC3FKdTTCKOdLRXI/ec1H3BgpkKuia9miI7E0F\nrWnvqVXPL5bNqk+YwVX/SUgXNsMCpREebvmSA1qMrsLnPNkm06veMqvelttydo4B\nurU48M8ya7yDO9ctCFSw3K/+smrj0Qj9pE/iqT3zKK7BWYckfhtQQrnNj7LLMpMb\n0jeY5fpV2BDI7KM9xaso+69IQZ866/QyOJ/w3bX6v1pIuMStzAlm+fhLCo1hYiz8\nWZLrLKOMyFTDrRaHrV0It78E8Zc7EUCMz7m3sQ3Wrzso/bGatAY4039bzQK9l8dg\nvcOx4bdpAgMBAAECggEAVxluOVbMhecKA9Fe9xzAnCfStP83SI3KyYQplItvGQU7\nK2Cl7dbBvhKcbL7/rSj0xxqGtkNlS6UCGWp0lgvWFEjrxIaJNa2BDpzKm1YEu42H\n+DQpSTdmFRdbgIqg05c1vl9t0NlV+Qh+eAthu1maK0+Gl7si8UKeKSq2m2r7GtFJ\ny3Al5Y+7FWhDdQVIoKmnw562wKLvewzNhHQi/XGr4xzctI321EJ/nPqW2oVd4Z9b\n/vqFF1zYNlZ8hE2evIS/A0h/Efa+4XzcIffkizNKv9XHwtdk0yCRPt4lCAhKoGyS\nFjbCBXaZ1mAwM+UFbp86KfmEwUH1YYufjk8cCNYozwKBgQDkLg5IANvx+IsUflXc\nKyYxi9VgK7WS2Ut9u/rrU1vxhRtDg99AyS8vkKFBKgM0nA8rHdNgktwE+z/xFfdx\nY5Stp5tXMj6FT6O+uDrnzul+k51OKH9P20JWTzE/hsgDCH88SdBClOYSbEY9gJ8z\nCH7JL1Kat2dpZIVKftEXDfPxHwKBgQDD4rhIJcmcizsUMGlb3WgWU8/ZN2jLv+1t\n7t89AX4bNeArN+Zj/gjTZoEC6J/Eei70qxbspBecm0OsuHnhoMjHUux99WzP9Z6U\nfLWN6BQZsVkqRLEgytPxCwkovlFF+52jANJCWqE8hFkJNu4FdG2WQwgC02mJXMKg\nMp1OwmUedwKBgBi75VBox26zQmA2UZhMFRfJ0JdcJZKFe2lltw1LO+wyQYJQCSM8\nq6C8TL6Dj1VklUBXO1J8mNzxXz0C5I+l+7fXMz+AcsaAm39Q+RGnnCfcWHDgcux1\nF/vDGdOJCKVLhn9CgRC2kznsArEoABnIEfY86vdaahtCijBJDuEw4gCBAoGAIv3O\nA31UjXVFoW6gc3uSi2J/X4MJYlQvmpKwKBqrJzsxhybeLgCEHRdTdmyNlbBp0OT7\nHFyXpy8JIMJ3azmohAqpGjsMK/3pTQcV+3p4lLpcfjN1HLF+uLFK+o88v26aEzMj\nXB0KbmAJ855vWGQa61ugA7k2QgZi8fD4rsgE/jMCgYBv3oykO6jrnhgriV0jtCgh\nYuqKUah/d9kinio4RYYb0Er9G31NtoVN+dzfugiwoF/mwXGMQmC+wygX0KsUvsF9\n6moeiuviFJ0yrCRgd/XNvDZEOkPPMvUkn+gcoaiux+sUWChjZILUtW7CyOuXtB4g\naH6VgyzaIJEgUjNwBaDneA==\n-----END PRIVATE KEY-----\n"
email="oleksandr-r@alexs-project-239406.iam.gserviceaccount.com"
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