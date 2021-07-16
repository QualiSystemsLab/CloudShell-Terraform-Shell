from collections import namedtuple
from typing import List, Dict

from cloudshell.api.cloudshell_api import AttributeNameValue

from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from distutils.util import strtobool

TFVar = namedtuple('TFVar', ['name', 'value'])


class InputOutputService:
    def __init__(self, driver_helper: ShellHelperObject):
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
        'Terraform Inputs' is an optional attribute. The attribute is tests_helper_files CSV list of key=value.
        """
        tf_inputs_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.{ATTRIBUTE_NAMES.TF_INPUTS}"
        result = []

        if tf_inputs_attr in self._driver_helper.tf_service.attributes and \
                self._driver_helper.tf_service.attributes[tf_inputs_attr].strip():
            for kvp in self._driver_helper.tf_service.attributes[tf_inputs_attr].split(","):
                name, value = kvp.strip().split("=", 2)
                result.append(TFVar(name.strip(), value.strip()))

        return result

    def get_variables_from_custom_tags_attribute(self) -> dict:
        """
        'Custom Tags' is an optional attribute. The attribute is tests_helper_files CSV list of key=value.
        """
        ct_inputs_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.{ATTRIBUTE_NAMES.CT_INPUTS}"
        ct_inputs = self._driver_helper.tf_service.attributes[ct_inputs_attr]
        result = {}

        if not ct_inputs:
            return result
        key_values = ct_inputs.split(",")

        for item in key_values:
            parts = item.split("=")
            if len(parts) != 2:
                raise ValueError("Line must be comma-separated list of key=values: key1=val1,key2=val2...")

            key = parts[0].strip()
            val = parts[1].strip()

            result[key] = val

        return result

    def get_apply_tag_attribute(self) -> bool:
        """
        'Apply Tags' is an mandatory attribute. The attribute is a boolean used to decide if tags get applied to tf
        resources.
        """
        at_inputs_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.{ATTRIBUTE_NAMES.APPLY_TAGS}"
        result = strtobool(self._driver_helper.tf_service.attributes[at_inputs_attr])

        return result

    def try_decrypt_password(self, value) -> str:
        try:
            return self._driver_helper.api.DecryptPassword(value).Value
        except:
            return value

    def parse_and_save_outputs(self, unparsed_output_json: Dict) -> None:
        """
        Parse the raw json from "terraform output -json" and update service attributes that are mapped to specific outputs.
        If "Terraform Outputs" attribute exist then save all unmapped outputs on this attribute
        """
        # check if mapped output attributes exist in driver data model and if it does create an attribute update request
        attr_update_req = []
        unmaped_outputs = {}
        unmaped_sensitive_outputs = {}
        for output in unparsed_output_json:
            attr_name = f"{self._driver_helper.tf_service.cloudshell_model_name}.out_{output}"
            if attr_name in self._driver_helper.tf_service.attributes:
                attr_update_req.append(AttributeNameValue(attr_name, unparsed_output_json[output]['value']))
            elif unparsed_output_json[output]['sensitive']:
                unmaped_sensitive_outputs[output] = unparsed_output_json[output]
            else:
                unmaped_outputs[output] = unparsed_output_json[output]

        # if TF OUTPUTS or TF SENSITIVE OUTPUTS attributes exists then we want to save all unmapped outputs
        # to this attributes
        tf_out_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.{ATTRIBUTE_NAMES.TF_OUTPUTS}"
        tf_sensitive_out_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}." \
                                f"{ATTRIBUTE_NAMES.TF_SENSIITVE_OUTPUTS}"

        if tf_out_attr in self._driver_helper.tf_service.attributes:
            # parse unmapped outputs
            output_string = self._parse_outputs_to_csv(unmaped_outputs)
            # prepare update request for unmapped attributes
            attr_update_req.append(AttributeNameValue(tf_out_attr, output_string))

        if tf_sensitive_out_attr in self._driver_helper.tf_service.attributes:
            # parse sensitive unmapped outputs
            sensitive_output_string = self._parse_outputs_to_csv(unmaped_sensitive_outputs)
            # prepare update request for sensitive unmapped attributes
            attr_update_req.append(AttributeNameValue(tf_sensitive_out_attr, sensitive_output_string))

        # send attribute update request using CS API
        if attr_update_req:
            self._driver_helper.api.SetServiceAttributesValues(self._driver_helper.sandbox_id,
                                                               self._driver_helper.tf_service.name, attr_update_req)

    def _parse_outputs_to_csv(self, outputs: Dict) -> str:
        output_string = []
        for output in outputs:
            output_string += [(output + '=' + str(outputs[output]['value']))]
        return ",".join(output_string)
