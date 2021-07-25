class ServiceAttrHandler(object):
    def __init__(self, tf_service: any):
        self._tf_service = tf_service
        self._attributes = self._tf_service.attributes

    def get_attribute(self, attribute_name: str) -> str:
        if attribute_name in self._attributes:
            return self._attributes[attribute_name]
        if f"{self._tf_service.cloudshell_model_name}.{attribute_name}" in self._attributes:
            return self._attributes[f"{self._tf_service.cloudshell_model_name}.{attribute_name}"]
        return ""
