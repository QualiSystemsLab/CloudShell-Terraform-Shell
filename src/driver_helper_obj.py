from logging import Logger

from cloudshell.api.cloudshell_api import CloudShellAPISession

from data_model import TerraformService2G


class DriverHelperObject(object):

    def __init__(self, api: CloudShellAPISession, res_id: str, tf_service: TerraformService2G, logger: Logger):

        self.api = api
        self.res_id = res_id
        self.tf_service = tf_service
        self.logger = logger
