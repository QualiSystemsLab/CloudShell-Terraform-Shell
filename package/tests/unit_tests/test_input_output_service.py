from unittest import TestCase
from unittest.mock import Mock, MagicMock

from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.services.input_output_service import InputOutputService, TFVar


class TestInputOutputService(TestCase):

    def test_try_decrypt_password_for_unencrypted_value(self):
        # arrange
        driver_helper = Mock()
        driver_helper.api.DecryptPassword.side_effect = Exception()
        input_output_service = InputOutputService(driver_helper, {}, {})
        value = Mock()

        # act
        result = input_output_service.try_decrypt_password(value)

        # assert
        self.assertEqual(value, result)

    def test_try_decrypt_password_for_encrypted_value(self):
        # arrange
        api_result = Mock()
        driver_helper = Mock()
        driver_helper.api.DecryptPassword.return_value = api_result
        input_output_service = InputOutputService(driver_helper, {}, {})
        value = Mock()

        # act
        result = input_output_service.try_decrypt_password(value)

        # assert
        self.assertEqual(api_result.Value, result)

    def test_get_variables_from_var_attributes_model_name_contains_uppercase(self):
        def get_attribute_mock(*args, **kwargs):
            return driver_helper.tf_service.attributes.get(args[0], "")

        # arrange
        driver_helper = Mock()
        driver_helper.tf_service.cloudshell_model_name = "TF Service"
        var_name = f"{driver_helper.tf_service.cloudshell_model_name}.MyVar_tfvar"
        driver_helper.tf_service.attributes = {"attribute1": "val1",
                                               "attribute2": "val2",
                                               var_name: "val3"}
        driver_helper.attr_handler.get_attribute.side_effect = get_attribute_mock

        input_output_service = InputOutputService(driver_helper, {}, {})
        input_output_service.try_decrypt_password = Mock(side_effect=TestHelper.return_original_val)

        # act
        result = input_output_service.get_variables_from_tfvar_attributes()

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "MyVar")
        self.assertEqual(result[0].value, "val3")

    def test_get_variables_from_terraform_input_attribute(self):
        def get_tf_inputs_attribute(*args, **kwargs):
            if args[0] == ATTRIBUTE_NAMES.TF_INPUTS:
                return "key1=val1,key2 = val2, key3=val3"
            return ""

        # arrange
        driver_helper = Mock()
        driver_helper.attr_handler.get_attribute.side_effect = get_tf_inputs_attribute
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        result = input_output_service.get_variables_from_terraform_input_attribute()

        # assert
        self.assertEqual(len(result), 3)
        self.assertIn(TFVar("key1", "val1"), result)
        self.assertIn(TFVar("key2", "val2"), result)
        self.assertIn(TFVar("key3", "val3"), result)

    def test_get_variables_from_terraform_input_attribute_doesnt_exist(self):
        # arrange
        driver_helper = Mock()
        driver_helper.attr_handler.get_attribute.return_value = ""
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        result = input_output_service.get_variables_from_terraform_input_attribute()

        # assert
        self.assertEqual(len(result), 0)

    def test_parse_and_save_outputs_no_mapped_attributes_and_no_outputs_attribute(self):
        # arrange
        driver_helper = Mock()
        driver_helper.tf_service.attributes = MagicMock()
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        input_output_service.parse_and_save_outputs({})

        # assert
        driver_helper.api.SetServiceAttributesValues.assert_not_called()

    def test_parse_and_save_outputs_with_mapped_attributes(self):
        # arrange
        driver_helper = Mock()
        var_name = f"{driver_helper.tf_service.cloudshell_model_name}.MyVar_tfout"
        driver_helper.tf_service.attributes = {
            var_name: "val1"
        }
        json_output = {
            "MyVar": {
                "sensitive": False,
                "type": "string",
                "value": "val1"
            }
        }
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        input_output_service.parse_and_save_outputs(json_output)

        # assert
        driver_helper.api.SetServiceAttributesValues.assert_called_once()

        self.assertEqual(driver_helper.api.SetServiceAttributesValues.call_args[0][2][0].Name, var_name)
        self.assertEqual(driver_helper.api.SetServiceAttributesValues.call_args[0][2][0].Value, "val1")

    def test_parse_and_save_outputs_with_mapped_attributes_and_outputs_attribute(self):
        # arrange
        driver_helper = Mock()
        var_name = f"{driver_helper.tf_service.cloudshell_model_name}.MyVar1_tfout"
        tf_output_name = f"{driver_helper.tf_service.cloudshell_model_name}.Terraform Outputs"
        driver_helper.tf_service.attributes = {
            var_name: "val1",
            tf_output_name: ""
        }
        json_output = {
            "MyVar1": {
                "sensitive": False,
                "type": "string",
                "value": "val1"
            },
            "MyVar2": {
                "sensitive": False,
                "type": "string",
                "value": "val2"
            },
            "MyVar3": {
                "sensitive": False,
                "type": "string",
                "value": "val3"
            }
        }
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        input_output_service.parse_and_save_outputs(json_output)

        # assert
        driver_helper.api.SetServiceAttributesValues.assert_called_once()
        # check that SetServiceAttributesValues was called with 2 AttributeNameValue values
        self.assertEqual(len(driver_helper.api.SetServiceAttributesValues.call_args[0][2]), 2)

    def test_parse_and_save_outputs_with_unmapped_attributes(self):
        # arrange
        driver_helper = Mock()
        tf_output_name = f"{driver_helper.tf_service.cloudshell_model_name}.Terraform Outputs"
        tf_sensitive_output_name = f"{driver_helper.tf_service.cloudshell_model_name}.Terraform Sensitive Outputs"
        driver_helper.tf_service.attributes = {
            tf_output_name: "",
            tf_sensitive_output_name: ""
        }
        json_output = {
            "MyVar1": {
                "sensitive": False,
                "type": "string",
                "value": "val1"
            },
            "MyVar2": {
                "sensitive": True,
                "type": "string",
                "value": "val2"
            },
            "MyVar3": {
                "sensitive": False,
                "type": "string",
                "value": "val3"
            }
        }
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        input_output_service.parse_and_save_outputs(json_output)

        # assert
        driver_helper.api.SetServiceAttributesValues.assert_called_once()

        attribute_update_req_list = driver_helper.api.SetServiceAttributesValues.call_args[0][2]
        sensitive_output_update_req = next(
            filter(lambda x: x.Name == tf_sensitive_output_name, attribute_update_req_list))

        attribute_update_req = driver_helper.api.SetServiceAttributesValues.call_args[0][2][0]
        self.assertEqual("MyVar2=val2", sensitive_output_update_req.Value)
        self.assertIn("MyVar1=val1", attribute_update_req.Value)
        self.assertIn("MyVar3=val3", attribute_update_req.Value)

    def test_parse_and_save_outputs_optional_tf_outputs_attributes(self):
        # arrange
        driver_helper = Mock()
        driver_helper.tf_service.attributes = {}
        json_output = {
            "MyVar1": {
                "sensitive": False,
                "type": "string",
                "value": "val1"
            },
            "MyVar2": {
                "sensitive": True,
                "type": "string",
                "value": "val2"
            }
        }
        input_output_service = InputOutputService(driver_helper, {}, {})

        # act
        input_output_service.parse_and_save_outputs(json_output)

        # assert
        driver_helper.api.SetServiceAttributesValues.assert_not_called()

    def test_parse_and_save_outputs_with_explicitly_mapped_outputs(self):
        # arrange
        def check_2nd_gen_attribute_exist(*args, **kwargs):
            return args[0] in driver_helper.tf_service.attributes

        driver_helper = Mock()
        driver_helper.attr_handler.check_2nd_gen_attribute_exist.side_effect = check_2nd_gen_attribute_exist
        driver_helper.attr_handler.get_2nd_gen_attribute_full_name.side_effect = TestHelper.return_original_val
        driver_helper.tf_service.attributes = {
            "attribute1": "",
            "attribute2": ""
        }
        json_output = {
            "MyVar": {
                "sensitive": False,
                "type": "string",
                "value": "val1"
            }
        }
        outputs_map = {
            "MyVar": "attribute1"
        }
        input_output_service = InputOutputService(driver_helper, {}, outputs_map)

        # act
        input_output_service.parse_and_save_outputs(json_output)

        # assert
        driver_helper.api.SetServiceAttributesValues.assert_called_once()

        self.assertEqual(driver_helper.api.SetServiceAttributesValues.call_args[0][2][0].Name, "attribute1")
        self.assertEqual(driver_helper.api.SetServiceAttributesValues.call_args[0][2][0].Value, "val1")

    def test_get_variables_from_explicitly_mapped_attributes(self):
        # arrange
        def attribute_exists_mock(*args, **kwargs):
            return args[0] in attributes

        def get_attribute_mock(*args, **kwargs):
            return attributes.get(args[0], "")

        attributes = {"attribute1": "val1",
                      "attribute2": "val2",
                      "attribute3": "val3",
                      "attribute4": "val4"}
        driver_helper = Mock()
        driver_helper.attr_handler.check_attribute_exist.side_effect = attribute_exists_mock
        driver_helper.attr_handler.get_attribute.side_effect = get_attribute_mock
        inputs_map = {"attribute2": "tfvar1",
                      "attribute4": "tfvar2"}
        input_output_service = InputOutputService(driver_helper, inputs_map, {})
        input_output_service.try_decrypt_password = Mock(side_effect=TestHelper.return_original_val)

        # act
        result = input_output_service.get_variables_from_explicitly_mapped_attributes()

        # assert
        self.assertIn(TFVar("tfvar1", "val2"), result)
        self.assertIn(TFVar("tfvar2", "val4"), result)

    def test_get_variables_from_explicitly_mapped_attributes_no_map(self):
        # arrange
        input_output_service = InputOutputService(Mock(), {}, {})

        # act
        result = input_output_service.get_variables_from_explicitly_mapped_attributes()

        # assert
        self.assertEqual(result, [])


class TestHelper:
    @staticmethod
    def return_original_val(*args, **kwargs):
        return args[0]
