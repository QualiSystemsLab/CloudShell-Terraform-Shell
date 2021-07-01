from collections import namedtuple
from typing import List, Dict

from cloudshell.api.cloudshell_api import AttributeNameValue

from driver_helper_obj import DriverHelperObject

TFVar = namedtuple('TFVar', ['name', 'value'])


class InputOutputService:
    def __init__(self, driver_helper: DriverHelperObject):
        self._driver_helper = driver_helper

    def get_variables_from_var_attributes(self) -> List[TFVar]:
        """
        Return list of TFVar based on attributes that start with "var_" (case insensitive).
        Password attributes will be automatically decrypted
        """
        # find all attributes that start with "var_"
        var_prefix = f"{self._driver_helper.tf_service.cloudshell_model_name}.var_"
        var_prefix_lower = var_prefix.lower()
        tf_vars = filter(lambda x: x.lower().startswith(var_prefix_lower),
                         self._driver_helper.tf_service.attributes.keys())

        result = []

        # add variable specific attributes to result
        for var in tf_vars:
            # remove the prefix to get the TF variable name
            value = self._driver_helper.tf_service.attributes[var]
            value = self.try_decrypt_password(value)
            tf_var = var.replace(var_prefix, "")

            self._driver_helper.logger.info(f"var={var}")
            self._driver_helper.logger.info(f"tf_var={tf_var}")
            self._driver_helper.logger.info(f"var_prefix={var_prefix}")
            self._driver_helper.logger.info(f"value={value}")

            result.append(TFVar(tf_var, value))

        return result

    def get_variables_from_terraform_input_attribute(self) -> List[TFVar]:
        """
        'Terraform Inputs' is an optional attribute. The attribute is a CSV list of key=value.
        """
        tf_inputs_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.Terraform Inputs"
        result = []

        if tf_inputs_attr in self._driver_helper.tf_service.attributes and \
                self._driver_helper.tf_service.attributes[tf_inputs_attr].strip():
            for kvp in self._driver_helper.tf_service.attributes[tf_inputs_attr].split(","):
                name, value = kvp.strip().split("=", 2)
                result.append(TFVar(name.strip(), value.strip()))

        return result

    def try_decrypt_password(self, value) -> str:
        try:
            return self._driver_helper.api.DecryptPassword(value).Value
        except:
            return value

    def parse_and_save_outputs(self, unparsed_output_json: Dict) -> None:
        """
        Parse the raw json from "terraform output -json" and update service attributes that are mapped to specific outputs.
        If "Terraform Output" attribute exist then save all unmapped outputs on this attribute
        """
        # check if output exists in driver data model and if it does create an attribute update request
        attr_update_req = []
        unmaped_outputs = {}
        for output in unparsed_output_json:
            attr_name = f"{self._driver_helper.tf_service.cloudshell_model_name}.out_{output}"
            if attr_name in self._driver_helper.tf_service.attributes:
                attr_update_req.append(AttributeNameValue(attr_name, unparsed_output_json[output]['value']))
            else:
                unmaped_outputs[output] = unparsed_output_json[output]

        # if "Terraform Output" attribute exists then we want to save all unmapped outputs to this attribute
        tf_out_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.Terraform Output"
        if tf_out_attr in self._driver_helper.tf_service.attributes:
            # parse unmapped outputs
            output_string = []
            for output in unmaped_outputs:
                if unmaped_outputs[output]['sensitive']:
                    # mask sensitive output for unmapped outputs
                    unmaped_outputs[output]['value'] = '(sensitive)'

                output_string += [(output + '=' + str(unmaped_outputs[output]['value']))]

            # prepare update request for unmapped attributes
            attr_update_req.append(AttributeNameValue(tf_out_attr, ",".join(output_string)))

        # send attribute update request using CS API
        if attr_update_req:
            self._driver_helper.api.SetServiceAttributesValues(self._driver_helper.res_id,
                                                               self._driver_helper.tf_service.name, attr_update_req)
