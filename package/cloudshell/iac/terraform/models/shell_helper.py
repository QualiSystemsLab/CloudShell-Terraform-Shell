from logging import Logger

from cloudshell.api.cloudshell_api import CloudShellAPISession


class ShellHelperObject(object):

    def __init__(self, api: CloudShellAPISession, res_id: str, tf_service: any, logger: Logger):
        self.api = api
        self.sandbox_id = res_id
        self.tf_service = tf_service
        self.logger = logger
