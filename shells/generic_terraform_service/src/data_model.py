from cloudshell.shell.core.driver_context import ResourceCommandContext, AutoLoadDetails, AutoLoadAttribute, \
    AutoLoadResource
from collections import defaultdict


class LegacyUtils(object):
    def __init__(self):
        self._datamodel_clss_dict = self.__generate_datamodel_classes_dict()

    def migrate_autoload_details(self, autoload_details, context):
        model_name = context.resource.model
        root_name = context.resource.name
        root = self.__create_resource_from_datamodel(model_name, root_name)
        attributes = self.__create_attributes_dict(autoload_details.attributes)
        self.__attach_attributes_to_resource(attributes, '', root)
        self.__build_sub_resoruces_hierarchy(root, autoload_details.resources, attributes)
        return root

    def __create_resource_from_datamodel(self, model_name, res_name):
        return self._datamodel_clss_dict[model_name](res_name)

    def __create_attributes_dict(self, attributes_lst):
        d = defaultdict(list)
        for attribute in attributes_lst:
            d[attribute.relative_address].append(attribute)
        return d

    def __build_sub_resoruces_hierarchy(self, root, sub_resources, attributes):
        d = defaultdict(list)
        for resource in sub_resources:
            splitted = resource.relative_address.split('/')
            parent = '' if len(splitted) == 1 else resource.relative_address.rsplit('/', 1)[0]
            rank = len(splitted)
            d[rank].append((parent, resource))

        self.__set_models_hierarchy_recursively(d, 1, root, '', attributes)

    def __set_models_hierarchy_recursively(self, dict, rank, manipulated_resource, resource_relative_addr, attributes):
        if rank not in dict: # validate if key exists
            pass

        for (parent, resource) in dict[rank]:
            if parent == resource_relative_addr:
                sub_resource = self.__create_resource_from_datamodel(
                    resource.model.replace(' ', ''),
                    resource.name)
                self.__attach_attributes_to_resource(attributes, resource.relative_address, sub_resource)
                manipulated_resource.add_sub_resource(
                    self.__slice_parent_from_relative_path(parent, resource.relative_address), sub_resource)
                self.__set_models_hierarchy_recursively(
                    dict,
                    rank + 1,
                    sub_resource,
                    resource.relative_address,
                    attributes)

    def __attach_attributes_to_resource(self, attributes, curr_relative_addr, resource):
        for attribute in attributes[curr_relative_addr]:
            setattr(resource, attribute.attribute_name.lower().replace(' ', '_'), attribute.attribute_value)
        del attributes[curr_relative_addr]

    def __slice_parent_from_relative_path(self, parent, relative_addr):
        if parent is '':
            return relative_addr
        return relative_addr[len(parent) + 1:] # + 1 because we want to remove the seperator also

    def __generate_datamodel_classes_dict(self):
        return dict(self.__collect_generated_classes())

    def __collect_generated_classes(self):
        import sys, inspect
        return inspect.getmembers(sys.modules[__name__], inspect.isclass)


class GenericTerraformService(object):
    def __init__(self, name):
        """
        
        """
        self.attributes = {}
        self.resources = {}
        self._cloudshell_model_name = 'Generic Terraform Service'
        self._name = name

    def add_sub_resource(self, relative_path, sub_resource):
        self.resources[relative_path] = sub_resource

    @classmethod
    def create_from_context(cls, context):
        """
        Creates an instance of NXOS by given context
        :param context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :return:
        :rtype GenericTerraformService
        """
        result = GenericTerraformService(name=context.resource.name)
        for attr in context.resource.attributes:
            result.attributes[attr] = context.resource.attributes[attr]
        return result

    def create_autoload_details(self, relative_path=''):
        """
        :param relative_path:
        :type relative_path: str
        :return
        """
        resources = [AutoLoadResource(model=self.resources[r].cloudshell_model_name,
            name=self.resources[r].name,
            relative_address=self._get_relative_path(r, relative_path))
            for r in self.resources]
        attributes = [AutoLoadAttribute(relative_path, a, self.attributes[a]) for a in self.attributes]
        autoload_details = AutoLoadDetails(resources, attributes)
        for r in self.resources:
            curr_path = relative_path + '/' + r if relative_path else r
            curr_auto_load_details = self.resources[r].create_autoload_details(curr_path)
            autoload_details = self._merge_autoload_details(autoload_details, curr_auto_load_details)
        return autoload_details

    def _get_relative_path(self, child_path, parent_path):
        """
        Combines relative path
        :param child_path: Path of a model within it parent model, i.e 1
        :type child_path: str
        :param parent_path: Full path of parent model, i.e 1/1. Might be empty for root model
        :type parent_path: str
        :return: Combined path
        :rtype str
        """
        return parent_path + '/' + child_path if parent_path else child_path

    @staticmethod
    def _merge_autoload_details(autoload_details1, autoload_details2):
        """
        Merges two instances of AutoLoadDetails into the first one
        :param autoload_details1:
        :type autoload_details1: AutoLoadDetails
        :param autoload_details2:
        :type autoload_details2: AutoLoadDetails
        :return:
        :rtype AutoLoadDetails
        """
        for attribute in autoload_details2.attributes:
            autoload_details1.attributes.append(attribute)
        for resource in autoload_details2.resources:
            autoload_details1.resources.append(resource)
        return autoload_details1

    @property
    def cloudshell_model_name(self):
        """
        Returns the name of the Cloudshell model
        :return:
        """
        return 'GenericTerraformService'

    @property
    def github_terraform_module_url(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Github Terraform Module URL'] if 'Generic Terraform Service.Github Terraform Module URL' in self.attributes else None

    @github_terraform_module_url.setter
    def github_terraform_module_url(self, value):
        """
        Github url to the Terraform module. Supports the same URL format from a browser. The entire repo will be downloaded. Url to a folder: https://github.com/<ACCOUNT>/<REPO>/tree/<BRANCH>/<PATH_TO_FOLDER> or url to a TF file: https://github.com/<ACCOUNT>/<REPO>/blob/<BRANCH>/<PATH>/filename.tf
        :type value: str
        """
        self.attributes['Generic Terraform Service.Github Terraform Module URL'] = value

    @property
    def terraform_version(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Terraform Version'] if 'Generic Terraform Service.Terraform Version' in self.attributes else None

    @terraform_version.setter
    def terraform_version(self, value):
        """
        The version of terraform needed (empty=latest). E.g. '1.0.0'
        :type value: str
        """
        self.attributes['Generic Terraform Service.Terraform Version'] = value

    @property
    def github_token(self):
        """
        :rtype: string
        """
        return self.attributes['Generic Terraform Service.Github Token'] if 'Generic Terraform Service.Github Token' in self.attributes else None

    @github_token.setter
    def github_token(self, value):
        """
        Github Token
        :type value: string
        """
        self.attributes['Generic Terraform Service.Github Token'] = value

    @property
    def cloud_provider(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Cloud Provider'] if 'Generic Terraform Service.Cloud Provider' in self.attributes else None

    @cloud_provider.setter
    def cloud_provider(self, value):
        """
        Cloud provider name to be used for cloud access
        :type value: str
        """
        self.attributes['Generic Terraform Service.Cloud Provider'] = value

    @property
    def uuid(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.UUID'] if 'Generic Terraform Service.UUID' in self.attributes else None

    @uuid.setter
    def uuid(self, value):
        """
        UUID for the driver instance. Used internally by the Terraform Shell, should not be a user input.
        :type value: str
        """
        self.attributes['Generic Terraform Service.UUID'] = value

    @property
    def branch(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Branch'] if 'Generic Terraform Service.Branch' in self.attributes else None

    @branch.setter
    def branch(self, value):
        """
        Overrides the branch in the the Module URL.
        :type value: str
        """
        self.attributes['Generic Terraform Service.Branch'] = value

    @property
    def terraform_outputs(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Terraform Outputs'] if 'Generic Terraform Service.Terraform Outputs' in self.attributes else None

    @terraform_outputs.setter
    def terraform_outputs(self, value):
        """
        Non-sensitive outputs from Terraform apply. All unmapped outputs will be stored here.
        :type value: str
        """
        self.attributes['Generic Terraform Service.Terraform Outputs'] = value

    @property
    def terraform_sensitive_outputs(self):
        """
        :rtype: string
        """
        return self.attributes['Generic Terraform Service.Terraform Sensitive Outputs'] if 'Generic Terraform Service.Terraform Sensitive Outputs' in self.attributes else None

    @terraform_sensitive_outputs.setter
    def terraform_sensitive_outputs(self, value):
        """
        Sensitive outputs from Terraform apply. All unmapped outputs will be stored here.
        :type value: string
        """
        self.attributes['Generic Terraform Service.Terraform Sensitive Outputs'] = value

    @property
    def terraform_inputs(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Terraform Inputs'] if 'Generic Terraform Service.Terraform Inputs' in self.attributes else None

    @terraform_inputs.setter
    def terraform_inputs(self, value):
        """
        Comma separated name=value list (e.g. varname1=varvalue1,varname2=varvalue2...)
        :type value: str
        """
        self.attributes['Generic Terraform Service.Terraform Inputs'] = value

    @property
    def remote_state_provider(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Remote State Provider'] if 'Generic Terraform Service.Remote State Provider' in self.attributes else None

    @remote_state_provider.setter
    def remote_state_provider(self, value):
        """
        Remote State provider resource name (only used if filled)
        :type value: str
        """
        self.attributes['Generic Terraform Service.Remote State Provider'] = value

    @property
    def custom_tags(self):
        """
        :rtype: str
        """
        return self.attributes['Generic Terraform Service.Custom Tags'] if 'Generic Terraform Service.Custom Tags' in self.attributes else None

    @custom_tags.setter
    def custom_tags(self, value):
        """
        Comma separated name=value list (e.g. varname1=varvalue1,varname2=varvalue2...)
        :type value: str
        """
        self.attributes['Generic Terraform Service.Custom Tags'] = value

    @property
    def apply_tags(self):
        """
        :rtype: bool
        """
        return self.attributes['Generic Terraform Service.Apply Tags'] if 'Generic Terraform Service.Apply Tags' in self.attributes else None

    @apply_tags.setter
    def apply_tags(self, value=True):
        """
        Should tags be applied? Yes=true, No=false (Default True)
        :type value: bool
        """
        self.attributes['Generic Terraform Service.Apply Tags'] = value

    @property
    def name(self):
        """
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        
        :type value: str
        """
        self._name = value

    @property
    def cloudshell_model_name(self):
        """
        :rtype: str
        """
        return self._cloudshell_model_name

    @cloudshell_model_name.setter
    def cloudshell_model_name(self, value):
        """
        
        :type value: str
        """
        self._cloudshell_model_name = value



