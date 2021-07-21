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
