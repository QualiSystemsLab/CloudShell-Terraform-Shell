import re
from collections import namedtuple
from typing import List, Dict

from cloudshell.api.cloudshell_api import AttributeNameValue

from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject

TFVar = namedtuple('TFVar', ['name', 'value'])


class InputOutputService:
    def __init__(self, driver_helper: ShellHelperObject, inputs_map: Dict, outputs_map: Dict):
        self._driver_helper = driver_helper
        self._inputs_map = inputs_map
        self._outputs_map = outputs_map

        self._var_postfix_regex = re.compile(f"{self._driver_helper.tf_service.cloudshell_model_name}\.(.+)_tfvar",
                                             re.IGNORECASE)

    def get_all_terrafrom_variables(self) -> List[TFVar]:
        # get variables from attributes that should be mapped to TF variables
        tf_vars = self.get_variables_from_tfvar_attributes()
        # get any additional TF variables from "Terraform Inputs" variable
        tf_vars.extend(self.get_variables_from_terraform_input_attribute())
        # get variables from explicitly mapped attributes
        tf_vars.extend(self.get_variables_from_explicitly_mapped_attributes())
        return tf_vars

    def get_variables_from_tfvar_attributes(self) -> List[TFVar]:
        """
        Return list of TFVar based on attributes that end with "_tfvar" (case insensitive).
        Password attributes will be automatically decrypted
        """
        result = []

        # find all attributes that end with "_tfvar"
        for attribute_name in self._driver_helper.tf_service.attributes:
            # add tf variable specific attributes to result
            m = re.match(self._var_postfix_regex, attribute_name)
            if m:
                # remove the prefix to get the TF variable name
                value = self._driver_helper.attr_handler.get_attribute(attribute_name)
                tf_var_value = self.try_decrypt_password(value)
                tf_var_name = m.group(1)

                result.append(TFVar(tf_var_name, tf_var_value))

        return result

    def get_variables_from_explicitly_mapped_attributes(self) -> List[TFVar]:
        """
        Return list of TFVar objects based on "inputs_map" dictionary of attribute names to TF variable names.
        Attribute names anc TF variables names are case sensitive.
        Password attributes will be automatically decrypted.
        """
        result = []
        self._driver_helper.logger.info(f"inputs_map: {self._inputs_map}")
        if not self._inputs_map:
            return result

        for attribute_name in self._inputs_map:
            if self._driver_helper.attr_handler.check_attribute_exist(attribute_name):
                attribute_value = self._driver_helper.attr_handler.get_attribute(attribute_name)
                attribute_value = self.try_decrypt_password(attribute_value)
                tf_var = self._inputs_map[attribute_name]
                result.append(TFVar(tf_var, attribute_value))
            else:
                raise ValueError(f"Mapped attribute {attribute_name} doesn't exist on "
                                 f"service {self._driver_helper.tf_service.name}")

        return result

    def get_variables_from_terraform_input_attribute(self) -> List[TFVar]:
        """
        'Terraform Inputs' is an optional attribute. The attribute is tests_helper_files CSV list of key=value.
        """
        result = []
        tf_inputs_attr = self._driver_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.TF_INPUTS).strip()

        if tf_inputs_attr:
            for kvp in tf_inputs_attr.split(","):
                name, value = kvp.strip().split("=", 1)
                result.append(TFVar(name.strip(), value.strip()))

        return result

    def get_tags_from_custom_tags_attribute(self) -> Dict[str, str]:
        """
        'Custom Tags' is an optional attribute. The attribute is tests_helper_files CSV list of key=value.
        """
        ct_inputs = self._driver_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.CT_INPUTS)
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

    def try_decrypt_password(self, value: str) -> str:
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
        self._driver_helper.logger.info(f"outputs_map: {self._outputs_map}")

        for output in unparsed_output_json:
            regex = re.compile(f"^{self._driver_helper.tf_service.cloudshell_model_name}\.{output}_tfout$",
                               re.IGNORECASE)
            matched_attr_name = None
            for attr_name in self._driver_helper.tf_service.attributes:
                if re.match(regex, attr_name):
                    matched_attr_name = attr_name
                    break

            if matched_attr_name:
                attr_update_req.append(AttributeNameValue(matched_attr_name, unparsed_output_json[output]['value']))

            if self._is_explicitly_mapped_output(output):
                mapped_attr_name = self._driver_helper.attr_handler.\
                    get_2nd_gen_attribute_full_name(self._outputs_map[output])
                attr_update_req.append(
                    AttributeNameValue(mapped_attr_name, unparsed_output_json[output]['value']))

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

    def _is_explicitly_mapped_output(self, output: str) -> bool:
        return self._outputs_map and output in self._outputs_map and \
            self._driver_helper.attr_handler.check_2nd_gen_attribute_exist(self._outputs_map[output])

    def _parse_outputs_to_csv(self, outputs: Dict) -> str:
        output_string = []
        for output in outputs:
            output_string += [(output + '=' + str(outputs[output]['value']))]
        return ",".join(output_string)
