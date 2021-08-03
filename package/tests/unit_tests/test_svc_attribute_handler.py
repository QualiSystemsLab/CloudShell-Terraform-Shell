import unittest

from mock import Mock

from cloudshell.iac.terraform.services.svc_attribute_handler import ServiceAttrHandler


class TestServiceAttrHandler(unittest.TestCase):
    def setUp(self) -> None:
        tf_service = Mock()
        self.svc_attribute_handler = ServiceAttrHandler(tf_service)

    def test_get_attribute(self):
        # arrange
        tf_service = Mock()
        tf_service.cloudshell_model_name = "cloudshell_model_name"
        tf_service.attributes = {
            "attribute_name": "attribute_value3",
            "cloudshell_model_name.attribute_name": "attribute_value4"
        }
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        attribute_value1 = svc_attribute_handler.get_attribute("")
        attribute_value2 = svc_attribute_handler.get_attribute("wrong_attribute_name")
        attribute_value3 = svc_attribute_handler.get_attribute("attribute_name")
        attribute_value4 = svc_attribute_handler.get_attribute("cloudshell_model_name.attribute_name")

        # assert
        self.assertEqual(attribute_value1, "")
        self.assertEqual(attribute_value2, "")
        self.assertEqual(attribute_value3, "attribute_value3")
        self.assertEqual(attribute_value4, "attribute_value4")

    def test_check_attribute_exist_1st_gen(self):
        # arrange
        tf_service = Mock()
        tf_service.cloudshell_model_name = "cloudshell_model_name"
        tf_service.attributes = {
            "attribute1": "attribute_value1",
            "cloudshell_model_name.attribute2": "attribute_value2"
        }
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        result = svc_attribute_handler.check_attribute_exist("attribute1")

        # assert
        self.assertTrue(result)

    def test_check_attribute_exist_2nd_gen(self):
        # arrange
        tf_service = Mock()
        tf_service.cloudshell_model_name = "cloudshell_model_name"
        tf_service.attributes = {
            "attribute1": "attribute_value1",
            "cloudshell_model_name.attribute2": "attribute_value2"
        }
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        result = svc_attribute_handler.check_attribute_exist("attribute2")

        # assert
        self.assertTrue(result)

    def test_check_attribute_doesnt_exist(self):
        # arrange
        tf_service = Mock()
        tf_service.cloudshell_model_name = "cloudshell_model_name"
        tf_service.attributes = {
            "attribute1": "attribute_value1",
            "cloudshell_model_name.attribute2": "attribute_value2"
        }
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        result = svc_attribute_handler.check_attribute_exist("attribute3")

        # assert
        self.assertFalse(result)

    def test_check_2nd_gen_attribute_exist_returns_true(self):
        # arrange
        tf_service = Mock()
        tf_service.cloudshell_model_name = "cloudshell_model_name"
        tf_service.attributes = {
            "attribute1": "attribute_value1",
            "cloudshell_model_name.attribute2": "attribute_value2"
        }
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        result = svc_attribute_handler.check_2nd_gen_attribute_exist("attribute2")

        # assert
        self.assertTrue(result)

    def test_check_2nd_gen_attribute_exist_returns_false(self):
        # arrange
        tf_service = Mock()
        tf_service.cloudshell_model_name = "cloudshell_model_name"
        tf_service.attributes = {
            "attribute1": "attribute_value1",
            "cloudshell_model_name.attribute2": "attribute_value2"
        }
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        result = svc_attribute_handler.check_2nd_gen_attribute_exist("attribute1")

        # assert
        self.assertFalse(result)

    def test_get_2nd_gen_attribute_full_name(self):
        # arrange
        tf_service = Mock()
        svc_attribute_handler = ServiceAttrHandler(tf_service)

        # act
        result = svc_attribute_handler.get_2nd_gen_attribute_full_name("attribute1")

        # assert
        self.assertEqual(f"{tf_service.cloudshell_model_name}.attribute1", result)
