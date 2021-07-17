import re
from collections import namedtuple
from typing import List, Dict

from cloudshell.api.cloudshell_api import AttributeNameValue

from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject

TFVar = namedtuple('TFVar', ['name', 'value'])


class InputOutputService:
    def __init__(self, driver_helper: ShellHelperObject, inputs_map: Dict = None, outputs_map: Dict = None):
        self._driver_helper = driver_helper
        self._inputs_map = inputs_map
        self._outputs_map = outputs_map

        self._var_postfix_regex = re.compile(f"{self._driver_helper.tf_service.cloudshell_model_name}\.(.+)_tfvar",
                                             re.IGNORECASE)

    def get_variables_from_tfvar_attributes(self) -> List[TFVar]:
        """
        Return list of TFVar based on attributes that end with "_tfvar" (case insensitive).
        Password attributes will be automatically decrypted
        """
        result = []

        # find all attributes that end with "_tfvar"
        for attribute_name in self._driver_helper.tf_service.attributes:
            # add tf variable specific attributes to result
            if m := re.match(self._var_postfix_regex, attribute_name):
                # remove the prefix to get the TF variable name
                value = self._driver_helper.tf_service.attributes[attribute_name]
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

        for attribute_name in self._inputs_map:
            if full_att_name := self._check_attribute_exist(attribute_name):
                pass
            else:
                raise ValueError(f"Mapped attribute {attribute_name} ")

        return result

    def _check_attribute_exist(self, attribute_name: str) -> str:
        if attribute_name in self._driver_helper.tf_service.attributes:
            return attribute_name
        elif (att := f"{self._driver_helper.tf_service.cloudshell_model_name}.{attribute_name}") in \
            self._driver_helper.tf_service.attributes:
            return att
        else:
            return None

    def get_variables_from_terraform_input_attribute(self) -> List[TFVar]:
        """
        'Terraform Inputs' is an optional attribute. The attribute is tests_helper_files CSV list of key=value.
        """
        tf_inputs_attr = f"{self._driver_helper.tf_service.cloudshell_model_name}.{ATTRIBUTE_NAMES.TF_INPUTS}"
        result = []

        if tf_inputs_attr in self._driver_helper.tf_service.attributes and \
                self._driver_helper.tf_service.attributes[tf_inputs_attr].strip():
            for kvp in self._driver_helper.tf_service.attributes[tf_inputs_attr].split(","):
                name, value = kvp.strip().split("=", 1)
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
        If "Terraform Outputs" attribute exist then save all unmapped outputs on this attribute
        """
        # check if mapped output attributes exist in driver data model and if it does create an attribute update request
        attr_update_req = []
        unmaped_outputs = {}
        unmaped_sensitive_outputs = {}

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
