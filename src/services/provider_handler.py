import os
from logging import Logger

from driver_helper_obj import DriverHelperObject

class ProviderHandler(object):
    def __init__(self, logger: Logger):
        self.logger = logger

    def initialize_provider(driver_help_object: DriverHelperObject):
        clp_resource_name = driver_help_object.tf_service.cloud_provider
        clp_res_model = driver_help_object.api.GetResourceDetails(clp_resource_name).ResourceModelName
        clpr_res_fam = driver_help_object.api.GetResourceDetails(clp_resource_name).ResourceFamilyName

        if clpr_res_fam != 'Cloud Provider' and clpr_res_fam != 'CS_CloudProvider':
            driver_help_object.logger.error(f"{clpr_res_fam} currently not supported")
            raise ValueError(f"{clpr_res_fam} currently not supported")

        try:
            if clp_res_model == 'Microsoft Azure' or clp_res_model == 'Microsoft Azure Cloud Provider Shell 2G':
                driver_help_object.api.WriteMessageToReservationOutput(driver_help_object.res_id,
                                                                       "Initializing provider...")
                driver_help_object.logger.info("Initializing Environment variables with CloudProvider details")
                clp_resource_attributes = driver_help_object.api.GetResourceDetails(clp_resource_name).ResourceAttributes
                for attr in clp_resource_attributes:
                    if attr.Name == "Azure Subscription ID":
                        os.environ["ARM_SUBSCRIPTION_ID"] = attr.Value
                    if attr.Name == "Azure Tenant ID":
                        os.environ["ARM_TENANT_ID"] = attr.Value
                    if attr.Name == "Azure Application ID":
                        os.environ["ARM_CLIENT_ID"] = attr.Value
                    if attr.Name == "Azure Application Key":
                        dec_client_secret = driver_help_object.api.DecryptPassword(attr.Value).Value
                        os.environ["ARM_CLIENT_SECRET"] = dec_client_secret
            else:
                driver_help_object.logger.error(f"{clp_res_model} currently not supported")
                raise ValueError(f"{clp_res_model} currently not supported")

        except Exception as e:
            driver_help_object.logger.error(f"Error Setting environment variables -> {str(e)}")
            raise
