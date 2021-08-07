import os

from dotenv import load_dotenv


class EnvVars(object):
    def __init__(self):
        load_dotenv()
        self.cs_user = os.environ.get("CS_USERNAME")
        self.cs_pass = os.environ.get("CS_PASSWORD")
        self.cs_server = os.environ.get("CS_SERVER")
        self.cs_domain = os.environ.get("RESERVATION_DOMAIN")
        self.cs_res_id = os.environ.get("RESERVATION_ID")
        self.sb_service_alias = os.environ.get("SB_SERVICE_ALIAS")
