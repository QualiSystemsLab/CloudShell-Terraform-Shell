from __future__ import annotations

from functools import lru_cache

from cloudshell.cp.terraform.exceptions import InvalidAppParamValue


class ResourceAttrRO(object):
    class NAMESPACE(object):
        SHELL_NAME = "shell_name"
        FAMILY_NAME = "family_name"

    def __init__(self, name, namespace, default=None):
        """Resource Attribute read-only.

        :param str name:
        :param str namespace:
        :param str default:
        """
        self.name = name
        self.namespace = namespace
        self.default = default

    def get_key(self, instance):
        """Get key.

        :param GenericResourceConfig instance:
        :rtype: str
        """
        return "{}.{}".format(getattr(instance, self.namespace), self.name)

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: str
        """
        if instance is None:
            return self

        return instance.attributes.get(self.get_key(instance), self.default)


class PasswordAttrRO(ResourceAttrRO):
    @lru_cache()
    def _decrypt_password(self, api, attr_value):
        """Decrypt password.

        :param cloudshell.api.cloudshell_api.CloudShellAPISession api:
        :param str attr_value:
        :return:
        """
        if api:
            return api.DecryptPassword(attr_value).Value
        raise InvalidAppParamValue("Cannot decrypt password, API is not defined")

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: str
        """
        val = super(PasswordAttrRO, self).__get__(instance, owner)
        if val is self or val is self.default:
            return val
        return self._decrypt_password(instance.api, val)


class ResourceListAttrRO(ResourceAttrRO):
    def __init__(self, name, namespace, sep=";", default=None):
        if default is None:
            default = []
        super(ResourceListAttrRO, self).__init__(name, namespace, default)
        self._sep = sep

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: list[str]
        """
        val = super(ResourceListAttrRO, self).__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        return list(filter(bool, map(str.strip, val.split(self._sep))))


class ResourceDictAttrRO(ResourceAttrRO):
    def __init__(self, name, namespace, line_sep=";", row_sep="=", default=None):
        if default is None:
            default = {}
        super(ResourceDictAttrRO, self).__init__(name, namespace, default)
        self._sep = line_sep
        self._row_sep = row_sep

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: list[str]
        """
        val = super(ResourceDictAttrRO, self).__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        values_list = list(filter(bool, map(str.strip, val.split(self._sep))))
        return dict(map(lambda x: x.strip().split(self._row_sep), values_list))


class ResourceBoolAttrRO(ResourceAttrRO):
    TRUE_VALUES = {"true", "yes", "y"}
    FALSE_VALUES = {"false", "no", "n"}

    def __init__(self, name, namespace, default=False):
        super(ResourceBoolAttrRO, self).__init__(name, namespace, default)

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: bool
        """
        val = super(ResourceBoolAttrRO, self).__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        if val.lower() in self.TRUE_VALUES:
            return True
        if val.lower() in self.FALSE_VALUES:
            return False
        raise ValueError("{} is boolean attr, but value is {}".format(self.name, val))


class ResourceAttrRODeploymentPath(ResourceAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH"):
        super().__init__(name, namespace)


class ResourcePasswordAttrRODeploymentPath(PasswordAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH"):
        super().__init__(name, namespace)


class ResourceBoolAttrRODeploymentPath(ResourceBoolAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)


class ResourceListAttrRODeploymentPath(ResourceListAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)


class ResourceDictAttrRODeploymentPath(ResourceDictAttrRO):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: dict[str, str]
        """
        val = super(ResourceDictAttrRO, self).__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        return dict(map(lambda x: x.strip().split("="), val.split(self._sep)))


class ResourceDictPasswordAttrRODeploymentPath(
    # ResourceDictAttrRO,
    ResourcePasswordAttrRODeploymentPath
):
    def __init__(self, name, namespace="DEPLOYMENT_PATH", *args, **kwargs):
        super().__init__(name, namespace, *args, **kwargs)

    def __get__(self, instance, owner):
        """Getter.

        :param GenericResourceConfig instance:
        :rtype: list[str]
        """
        val = super(PasswordAttrRO, self).__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        return dict(map(lambda x: x.strip().split("="), val.split(";")))


class TerraformDeploymentAppAttributeNames:
    git_token = "Git Token"
    git_terraform_url = "Git Terraform URL"
    branch = "Branch"
    terraform_inputs = "Terraform Inputs"
    terraform_sensitive_inputs = "Terraform Inputs"
    cloud_provider = "Cloud Provider"
    custom_tags = "Custom Tags"
    autogenerated_name = "Autogenerated Name"
