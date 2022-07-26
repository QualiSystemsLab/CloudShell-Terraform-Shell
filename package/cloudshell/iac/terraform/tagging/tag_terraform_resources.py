# entrypoint is package/cloudshell/iac/terraform/services/tf_proc_exec.py def tag_terraform

# tags changes

# - remove/comment out main (only uses start_tagging_terraform_resources function)
# - removed Settings class and related methods
# - add "from cloudshell.iac.terraform.models.exceptions import TerraformAutoTagsError"
# - verify imports are the same (need to add to dependencies file if different and require specific version)
# - modify logger to use logger from module
# - _perform_terraform_init_plan is heavily changed due to the fact we may need to run this on windows or linux

# modified methods:
# - init_logging
# - start_tagging_terraform_resources
# - _perform_terraform_init_plan
# - OverrideTagsTemplatesCreator

import argparse
import re
import enum
import traceback
from typing import List
import hcl2
import os
import subprocess
import logging
from inspect import getframeinfo, stack
from functools import wraps
import json

### Added
from cloudshell.iac.terraform.models.exceptions import TerraformAutoTagsError


# =====================================================================================================================

class Constants:
    TAGS = "tags"  # used for tag aws and azure resources in terraform
    LABELS = "labels"  # used for tag kubernetes resources in terraform
    OVERRIDE_LOG_FILE_NAME = "override_log"
    EXCLUDE_FROM_TAGGING_FILE_NAME = "exclude_from_tagging.json"  # modified

    @staticmethod
    def get_override_log_path(main_folder: str):
        return os.path.join(main_folder,
                            Constants.OVERRIDE_LOG_FILE_NAME)

    # modified
    @staticmethod
    def get_exclude_from_tagging_file_path(main_folder: str):
        return os.path.join(main_folder,
                            Constants.EXCLUDE_FROM_TAGGING_FILE_NAME)

# =====================================================================================================================


class ExceptionWrapper:
    @staticmethod
    def wrap_class(cls):
        for (attr_name, attr_value) in cls.__dict__.items():
            if not attr_name.startswith('__') and \
                    callable(attr_value) or (not callable(attr_value) and isinstance(attr_value, staticmethod)):
                setattr(cls, attr_name, ExceptionWrapper.wrap_func(attr_value))
        return cls

    @staticmethod
    def wrap_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if callable(func):  # for callable normal function
                    return func(*args, **kwargs)
                # for staticmethod (which by definition are not callable, but they hold the raw function in the __func__)
                else:
                    return func.__func__(*args, **kwargs)
            except Exception as e:
                caller = getframeinfo(stack()[1][0])
                code_line = caller.lineno
                trace = traceback.format_exc()
                LoggerHelper.write_error(f"An Unhandled exception that started in the line {code_line} was occurred,\n"
                                         f"Exception is:\n"
                                         f"{trace}\n\n", code_line)
                raise e

        return wrapper


# =====================================================================================================================

# modified
class LoggerHelper:
    log_instance = None

    @staticmethod
    def init_logging(logger: logging.Logger):
        LoggerHelper.log_instance = logger

    @staticmethod
    def write_info(msg: str, code_line: int = None):
        if code_line is None:
            caller = getframeinfo(stack()[1][0])
            code_line = caller.lineno
        LoggerHelper.log_instance.info(f" Line {code_line}]:  {msg}")

    @staticmethod
    def write_warning(msg: str, code_line: int = None):
        if code_line is None:
            caller = getframeinfo(stack()[1][0])
            code_line = caller.lineno
        LoggerHelper.log_instance.warning(f" Line {code_line}]:  {msg}")

    @staticmethod
    def write_error(msg: str, code_line: int = None):
        if code_line is None:
            caller = getframeinfo(stack()[1][0])
            code_line = caller.lineno
        LoggerHelper.log_instance.error(f" Line {code_line}]:  {msg}")


# =====================================================================================================================


class FileInfo:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_dir = os.path.dirname(file_path)

    def __str__(self):
        return self.file_name

    def __repr__(self):
        return self.file_name


class FilesHelper:
    @staticmethod
    def get_all_files(dir_path: str, file_extension: str = None) -> List[FileInfo]:
        files: List[FileInfo] = []
        for root, directories, file_names in os.walk(dir_path):
            for file_name in file_names:
                if file_extension:
                    if file_name.endswith(file_extension):
                        files.append(FileInfo(os.path.join(root, file_name)))
                else:
                    files.append(FileInfo(os.path.join(root, file_name)))
        return files


# =====================================================================================================================


class TerraformResource:
    def __init__(self, resource_type: str, resource_name: str, tags):
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.tags = tags


# =====================================================================================================================

# modified
@ExceptionWrapper.wrap_class
class OverrideTagsTemplatesCreator:
    def __init__(self, tags_dict: dict, terraform_version: str):
        # self.torque_tags_file_path = torque_tags_file_path
        self.torque_tags_dict = tags_dict
        self.torque_tags_flat_map = ""  # will be "map(<tag1Name>,<tag1Value>,...)" or "tomap({<tag1Name>=<tag1Value>,...})"
        self.torque_autoScaling_tags_flat_maps_list = ""  # will be list(<autoScalingTag1>,<autoScalingTag2>....) or tolist([<autoScalingTag1>, <autoScalingTag1>...])
        self._terraform_syntax = TerraformSyntaxVersion.get_terraform_syntax(terraform_version)
        self._map_key_value_separator = self._get_map_key_value_separator()

        if not self.torque_tags_dict:
            LoggerHelper.write_error(f"Didn't get tags dict, exiting the tagging process")
            return

        LoggerHelper.write_info(f"Initiate default tags templates")
        self._init_torque_tags_flat_map()
        self._init_torque_autoScaling_tags_flat_maps_list()

    def _get_map_key_value_separator(self):
        # In terraform 0.12.0 and above map is used as follows: "tomap({<tag1Name>=<tag1Value>,...})"
        if self._terraform_syntax == TerraformSyntaxVersion.zero_twelve_and_above:
            return '='
        # In terraform 0.11.x and below map is used as follows: "map(<tag1Name>,<tag1Value>,...)"
        return ','

    def _get_map_tags_template(self, map_values: str):
        # In terraform 0.12.0 and above map is used as follows: "tomap({<tag1Name>=<tag1Value>,...})"
        if self._terraform_syntax == TerraformSyntaxVersion.zero_twelve_and_above:
            return f"tomap({{{map_values}}})"
        # In terraform 0.11.x and below map is used as follows: "map(<tag1Name>,<tag1Value>,...)"
        return f"map({map_values})"

    def _get_list_tags_template(self, list_values: str):
        # In terraform 0.12.0 and above list is used as follows: "tolist([<tag1>, <tag2>...])"
        if self._terraform_syntax == TerraformSyntaxVersion.zero_twelve_and_above:
            return f"\ntolist([\n\t\t{list_values}\n])"
        # In terraform 0.11.x and below list is used as follows: "list(<tag1>,<tag2>....)"
        return f"\nlist(\n\t\t{list_values}\n)"

    def _get_terraform_syntax_string_template(self, terraform_str: str):
        # In version 0.11.x and below using terraform syntax like "map", "merge", "concat", and more
        # must be wrapped in "${}"
        if self._terraform_syntax == TerraformSyntaxVersion.zero_eleven_and_below:
            return f"\"${{{terraform_str}}}\""
        # In terraform 0.12.0 and above you can use terraform syntax as is
        return terraform_str

    def get_single_group_string(self, single_str: str):
        # In version 0.11.x and below using terraform syntax like "map", "merge", "concat", and more
        # must be wrapped in "${}"
        single_group_match = RegexHelper.get_single_group_match_from_regex_result(text=single_str,
                                                                        pattern=RegexHelper.SINGLE_VAR_PATTERN)
        # In terraform 0.12.0 and above you can call the string as is,
        # but it also excepts string interpolation syntax from terraform 0.11.0 and below
        if single_group_match is None and self._terraform_syntax == TerraformSyntaxVersion.zero_twelve_and_above:
            return single_str
        return single_group_match

    def _read_and_save_tags_from_file(self):
        with open(self.torque_tags_file_path) as tags_file:
            tags = json.load(tags_file)
            for k, v in tags.items():
                self.torque_tags_dict[k] = v

    def _init_torque_tags_flat_map(self):
        torque_tags_to_list = []
        for key, value in self.torque_tags_dict.items():
            torque_tags_to_list.append(f"\"{key}\"{self._map_key_value_separator}\"{value}\"")

        if not torque_tags_to_list:
            return
        map_value = " , ".join(torque_tags_to_list)
        self.torque_tags_flat_map = self._get_map_tags_template(map_value)

    def _init_torque_autoScaling_tags_flat_maps_list(self):
        torque_tags_to_list = []
        for key, value in self.torque_tags_dict.items():
            map_value = "\"key\"{0}\"{1}\",\"value\"{0}\"{2}\",\"propagate_at_launch\"{0}\"true\"". \
                format(self._map_key_value_separator, key, value)
            torque_tags_to_list.append(self._get_map_tags_template(map_value))

        if not torque_tags_to_list:
            return

        # All the \t and \n in here is just so that the override will look good and readable
        # (in case we need to look at it)
        list_of_maps_value = " ,\n\t\t".join(torque_tags_to_list)
        self.torque_autoScaling_tags_flat_maps_list = self._get_list_tags_template(list_of_maps_value)

    def _get_basic_override_tags_template(self, resource_type: str, resource_name: str, tags: str) -> str:
        tags_label = Constants.LABELS if resource_type.startswith("kubernetes_") else Constants.TAGS
        return """
resource \"{RESOURCE_TYPE}\" \"{RESOURCE_NAME}\" {{
    {TAGS_LABEL} = {TAGS_VALUE}
}}
\n""".format(RESOURCE_TYPE=resource_type,
             RESOURCE_NAME=resource_name,
             TAGS_LABEL=tags_label,
             TAGS_VALUE=tags)

    def get_merge_tags_template(self, resource_type: str, resource_name: str, client_str_tags: str) -> str:
        if not self.torque_tags_flat_map:
            return ""

        separator = ", " if not client_str_tags.replace(" ", "").endswith(",") else " "
        merge_str = f"merge({client_str_tags}{separator}{self.torque_tags_flat_map})"

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=self._get_terraform_syntax_string_template(merge_str))

    def get_concat_tags_template(self, resource_type: str, resource_name: str, client_str_tags: str) -> str:
        if not self.torque_autoScaling_tags_flat_maps_list:
            return ""

        separator = ", " if not client_str_tags.replace(" ", "").endswith(",") else " "
        concat_str = f"concat({client_str_tags}{separator}{self.torque_autoScaling_tags_flat_maps_list})"

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=self._get_terraform_syntax_string_template(concat_str))

    def get_torque_tags_with_client_dict_tags_template(self, resource_type: str, resource_name: str,
                                                       client_dict_tags: dict) -> str:
        tags = {} if not client_dict_tags else client_dict_tags
        # To add out tags to the client dict tags AND to OVERRIDE them in case we have the same tag names
        for key, value in self.torque_tags_dict.items():
            tags[key] = value

        all_tags_in_str_list = []
        for key, value in tags.items():
            all_tags_in_str_list.append(f"\"{key}\" = \"{value}\"")

        if not all_tags_in_str_list:
            return ""

        all_tags_as_str = ", ".join(all_tags_in_str_list)
        all_tags_as_str = f"{{{all_tags_as_str}}}"

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=all_tags_as_str)

    def get_torque_tags_with_autoscaling_client_dict_tags_template(self, resource_type: str, resource_name: str,
                                                                   client_list_dict_tags: list) -> str:
        list_of_tags_dict = [] if not client_list_dict_tags else client_list_dict_tags
        for key, value in self.torque_tags_dict.items():
            single_tag_dict = {"key": key, "value": value, "propagate_at_launch": "true"}
            list_of_tags_dict.append(single_tag_dict)

        all_tags_in_str_list = []
        for tag in list_of_tags_dict:
            all_tags_in_str_list.append(f"{{key = \"{tag['key']}\", value = \"{tag['value']}\","
                                        f" propagate_at_launch = \"{tag['propagate_at_launch']}\"}}")
        # All the \t and \n in here is just so that the override will look good and readable
        # (in case we need to look at it)
        all_tags_as_str = ",\n\t\t\t\t".join(all_tags_in_str_list)
        all_tags_as_str = f"[\n\t\t\t\t{all_tags_as_str}\n\t\t]"

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=all_tags_as_str)


# =====================================================================================================================

class TerraformSyntaxVersion(enum.Enum):
    zero_eleven_and_below = 0
    zero_twelve_and_above = 1

    @staticmethod
    def get_terraform_syntax(terraform_version: str):
        version_arr = terraform_version.split(".")
        if len(version_arr) == 3:
            if int(version_arr[0]) == 0:
                # If version is at most 0.11.x
                if int(version_arr[1]) <= 11:
                    return TerraformSyntaxVersion.zero_eleven_and_below
                # If version is at least 0.12.0
                else:
                    return TerraformSyntaxVersion.zero_twelve_and_above
            # Version is at least 1.x.x
            else:
                return TerraformSyntaxVersion.zero_twelve_and_above
        # If did not receive a valid version then return the default version syntax.
        else:
            return TerraformSyntaxVersion.zero_eleven_and_below


# =====================================================================================================================

@ExceptionWrapper.wrap_class
class Hcl2Parser:
    @staticmethod
    def get_tf_file_as_dict(tf_file_path: str) -> dict:
        try:
            with(open(tf_file_path, 'r')) as client_tf_file:
                return hcl2.load(client_tf_file)
        except:
            # logging the file path that encountered the error
            LoggerHelper.write_error(f"Failed to parse tf file '{tf_file_path}'")
            # re-raising the exception so it will break the flow and its details are logged by the ExceptionWrapper
            raise

    # full_resource_object contain many information in an unreadable structure
    # so we convert it to more less info with more readable structure
    @staticmethod
    def get_terraform_resource_safely(full_resource_object: dict) -> TerraformResource:
        if full_resource_object is None or not full_resource_object.keys():
            return None
        resource_type = next(iter(full_resource_object.keys()))

        if full_resource_object[resource_type] is None or not full_resource_object[resource_type].keys():
            return None
        resource_name = next(iter(full_resource_object[resource_type].keys()))

        tags = full_resource_object[resource_type][resource_name].get('tags', None)

        # before version 3.0.0 of hcl2, "tags" was a list and we took the first element in it
        # this behavior was changed here: https://github.com/amplify-education/python-hcl2/blob/master/CHANGELOG.md#300---2021-07-14
        if tags:
            # we replace ' with " becuase hc2l has some bug:
            #  for example it parse --> merge(local.common_tags, {"Name"="tomer"})
            # to --> merge(local.common_tags, {'Name'='tomer'})  and this is invalid syntax according to terraform
            if type(tags) is str:
                tags = tags.replace("'", "\"").replace(",,", ",")  # due to bug in hcl2 library

        return TerraformResource(resource_type=resource_type,
                                 resource_name=resource_name,
                                 tags=tags)

    @staticmethod
    def get_tf_file_resources(tf_file_path: str) -> List[TerraformResource]:
        tf_file_resources: List[TerraformResource] = []
        tf_as_dict = Hcl2Parser.get_tf_file_as_dict(tf_file_path)
        for resource_object in tf_as_dict.get("resource", []):
            tf_file_resources.append(Hcl2Parser.get_terraform_resource_safely(resource_object))
        return tf_file_resources


# =====================================================================================================================


class RegexHelper:
    # example: "${merge(<Map1>,<Map2>,....)}"   --->    group match: "<Map1>,<Map2>,...."
    # The terraform 'merge' is used to merge two maps (i.e dicts) (most common used is in the tags of all resources
    # (Except the autoscalling resource))
    MERGED_TAGS_PATTERN = r"^.*\bmerge\b[ ]*\((.*)\).*"

    # example: "${concat(<List1>,<List2>,....)}"   --->    group match: "<List1>,<List2>,...."
    # The terraform 'concat' is used to concat two list (most common used is in the tags of autoscalling resources
    # because the tags there represent as lists)
    CONCAT_LIST_TAGS_PATTERN = r"^.*\bconcat\b[ ]*\((.*)\).*"

    # example: "${locals.my_tags}"              --->    group match: "locals.my_tags"
    SINGLE_VAR_PATTERN = r"\$\{(.*)\}"

    # example:
    # Error: Unsupported argument
    #
    #   on main.tf line 40, in resource "aws_api_gateway_account" "agc":
    #   40:   tags        = local.my_tags
    #
    # An argument named "tags" is not expected here.  ---> group match: "aws_api_gateway_account"
    UNSUPPORTED_TAGS_OR_LABELS_PATTERN_1 = \
        r"^\bError: Unsupported argument\b[\n]*.*\bresource\b[ ]*\"(.*?)\".*[\n]*.*[\n]*.*\"(?:\btags\b|\blabels\b)\"[ ]*\bis not expected here\b"
    # In the above pattern we need to group the (?:\btags\b|\blabels\b) so we can match "tags" or "labels" but we don't
    # want this group to return as a group in the matches so we add the '?:' in the beginning to exclude this group
    # from the groups that return as matches

    # example:
    # Error: azurerm_mysql_firewall_rule.default: : invalid or unknown key: tags
    # ---> group match: "aws_api_gateway_account"
    UNSUPPORTED_TAGS_OR_LABELS_PATTERN_2 = r"^\bError\b[ ,:]*(.*?)\..*\binvalid or unknown\b.*\btags\b"

    @staticmethod
    def get_single_group_match_from_regex_result(text: str, pattern: str) -> str:
        regex_obj = re.compile(pattern)
        regex_result = regex_obj.search(text)
        if regex_result and regex_result.groups():
            return regex_result.groups()[0]
        return None

    @staticmethod
    def get_all_group_match_from_regex_result(text: str, patterns: List[str]) -> List[str]:
        all_matches: List[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.M)  # re.M = multi line matches (i.e include \n in the search)

            for match in matches:
                all_matches.append(match)

        return all_matches


# =====================================================================================================================

class ResourcesTagger:
    def __init__(self, tf_file_info: FileInfo, tags_creator: OverrideTagsTemplatesCreator):
        self.tf_file_info = tf_file_info
        self.tags_creator = tags_creator

    def _get_override_file_path(self):
        (file_without_ext, ext) = os.path.splitext(self.tf_file_info.file_name)
        override_file_path = os.path.join(self.tf_file_info.file_dir, f"{file_without_ext}_override.tf")
        return override_file_path

    def _get_torque_tags_with_client_string_tags(self, terraform_resource: TerraformResource) -> str:
        client_tags = terraform_resource.tags.replace("\n", "")

        # It's important that we search for MERGED_TAGS_PATTERN before we search for SINGLE_VAR_PATTERN because
        # the MERGED_TAGS_PATTERN can also be recognized as a SINGLE_VAR_PATTERN but we want to act differently if it is
        # MERGED_TAGS_PATTERN
        parsed_client_tags = RegexHelper.get_single_group_match_from_regex_result(text=client_tags,
                                                                                  pattern=RegexHelper.MERGED_TAGS_PATTERN)
        if not parsed_client_tags:  # if not find concat pattern then try to fall back to single var pattern
            parsed_client_tags = self.tags_creator.get_single_group_string(client_tags)

        # If succeed to find any pattern then create a new merge tags template
        if parsed_client_tags:
            return self.tags_creator.get_merge_tags_template(
                resource_type=terraform_resource.resource_type,
                resource_name=terraform_resource.resource_name,
                client_str_tags=parsed_client_tags)

        else:  # Otherwise raise an error
            raise Exception("Unable to process client tags")

    def _get_torque_tags_with_autoscaling_client_string_tags(self, terraform_resource: TerraformResource) -> str:
        client_tags = terraform_resource.tags.replace("\n", "")
        # Try at first to find a concat pattern.
        # It's important that we search for CONCAT_LIST_TAGS_PATTERN before we search for SINGLE_VAR_PATTERN because
        # the CONCAT_LIST_TAGS_PATTERN can also be recognized as a SINGLE_VAR_PATTERN but we want to act differently
        # if it is CONCAT_LIST_TAGS_PATTERN
        parsed_client_tags = RegexHelper.get_single_group_match_from_regex_result(text=client_tags,
                                                                                  pattern=RegexHelper.CONCAT_LIST_TAGS_PATTERN)
        if not parsed_client_tags:  # if not find concat pattern then try to fall back to single var pattern
            parsed_client_tags = self.tags_creator.get_single_group_string(client_tags)
        # If succeed to find any pattern then create a new concat tags template
        if parsed_client_tags:
            return self.tags_creator.get_concat_tags_template(
                resource_type=terraform_resource.resource_type,
                resource_name=terraform_resource.resource_name,
                client_str_tags=parsed_client_tags)
        else:  # Otherwise raise an error
            raise Exception("Unable to process client tags")

    def _get_torque_tags_with_client_dict_tags(self, terraform_resource: TerraformResource) -> str:
        return self.tags_creator.get_torque_tags_with_client_dict_tags_template(
            resource_type=terraform_resource.resource_type,
            resource_name=terraform_resource.resource_name,
            client_dict_tags=terraform_resource.tags)

    def _get_torque_tags_with_autoscaling_client_dict_tags(self, terraform_resource: TerraformResource) -> str:
        return self.tags_creator.get_torque_tags_with_autoscaling_client_dict_tags_template(
            resource_type=terraform_resource.resource_type,
            resource_name=terraform_resource.resource_name,
            client_list_dict_tags=terraform_resource.tags)

    def _add_tags_to_override_file(self, override_file_stream, terraform_resource: TerraformResource):
        if terraform_resource:
            # in case of autoscaling_group the tags look different.
            # see here : https://www.terraform.io/docs/providers/aws/r/autoscaling_group.html
            # and here: https://github.com/hashicorp/terraform/issues/15226
            if terraform_resource.resource_type == "aws_autoscaling_group":
                # if we don't have tags or the tags are list of dict like
                # [{key = "A", value = "B", propagate_at_launch =  "True"},
                # {key = "C" , value = "D", propagate_at_launch =  "True"}]
                if not terraform_resource.tags or type(terraform_resource.tags) is list:
                    override_file_stream.write(
                        self._get_torque_tags_with_autoscaling_client_dict_tags(terraform_resource))
                # i.e tags is most likely = "${concat(<List_of_maps1>,<List_of_maps2>,....)}" or "${<List_of_maps>}"
                elif type(terraform_resource.tags) is str:
                    override_file_stream.write(
                        self._get_torque_tags_with_autoscaling_client_string_tags(terraform_resource))
            else:
                # if we don't have tags or the tags are dict like "  key1="value1" , key2="value2"  "
                if not terraform_resource.tags or type(terraform_resource.tags) is dict:
                    override_file_stream.write(self._get_torque_tags_with_client_dict_tags(terraform_resource))
                # i.e tags is most likely = "${merge(<map1>,<map2>,....)}" or "${<map>}"
                elif type(terraform_resource.tags) is str:
                    override_file_stream.write(self._get_torque_tags_with_client_string_tags(terraform_resource))

    def create_override_file(self, untaggable_resources_types: List[str] = []):
        tf_file_resources = Hcl2Parser.get_tf_file_resources(self.tf_file_info.file_path)
        if not tf_file_resources or len(tf_file_resources) == 0:
            LoggerHelper.write_info(f"No need to create override file to {self.tf_file_info.file_name}"
                                    f" (0 resources found in tf)")
            return

        override_file_path = self._get_override_file_path()
        with(open(override_file_path, 'w')) as override_tf_file:
            for tf_resource in tf_file_resources:
                if tf_resource.resource_type not in untaggable_resources_types:
                    self._add_tags_to_override_file(override_tf_file, tf_resource)
        LoggerHelper.write_info(f"Override file was created to {self.tf_file_info.file_name}"
                                f" ({len(tf_file_resources)} resources found in tf)")


#
# =====================================================================================================================
#                                         M          A       I       N
# =====================================================================================================================


# modified
def _perform_terraform_init_plan(main_tf_dir_path: str, inputs_dict: dict):
    inputs = []
    for input_key, input_value in inputs_dict.items():
        inputs.extend(['-var', f'{input_key}={input_value}'])

    terraform_exe_path = f'{os.path.join(main_tf_dir_path, "terraform.exe")}'
    init_command = [terraform_exe_path, 'init', '-no-color']
    plan_command = [terraform_exe_path, 'plan', '-no-color', '-input=false']
    plan_command.extend(inputs)

    init = subprocess.Popen(init_command, cwd=main_tf_dir_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    init_stdout, init_stderr = init.communicate()

    if init_stderr:
        return init_stdout, init_stderr, init.returncode

    # Save the output to a var proc_stdout
    plan = subprocess.Popen(plan_command, cwd=main_tf_dir_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    plan_stdout, plan_stderr = plan.communicate()
    plan_stdout = ""
    return plan_stdout, plan_stderr, plan.returncode


def _get_untaggable_resources_types_from_plan_output(text: str) -> List[str]:
    untaggable_resources = RegexHelper.\
        get_all_group_match_from_regex_result(text=text,
                                              patterns=[RegexHelper.UNSUPPORTED_TAGS_OR_LABELS_PATTERN_1,
                                                        RegexHelper.UNSUPPORTED_TAGS_OR_LABELS_PATTERN_2])
    return untaggable_resources


# modified
def start_tagging_terraform_resources(main_dir_path: str, logger, tags_dict: dict, inputs_dict: dict = None,
                                      terraform_version: str = ""):
    if not os.path.exists(main_dir_path):
        raise TerraformAutoTagsError(f"Path {main_dir_path} does not exist")
    tfs_folder_path = main_dir_path
    exclude_from_tagging_file_path = Constants.get_exclude_from_tagging_file_path(main_dir_path)

    # modified
    LoggerHelper.init_logging(logger)

    LoggerHelper.write_info(f"Trying to preform terraform init & plan in the directory '{tfs_folder_path}'"
                            " in order to check for any validation errors in tf files")
    stdout, stderr, return_code = _perform_terraform_init_plan(tfs_folder_path, inputs_dict)  # modified
    if return_code != 0 or stderr:
        LoggerHelper.write_error("Exit before the override procedure began because the init/plan failed."
                                 f" (Return_code is {return_code})"
                                 f"\n\nErrors are:\n{stderr}\n")
        # Error Code 3 mark to the outside tf script (that run me) that there was an error but not because of
        # the override procedure (but because the client tf file has compile errors even before we started the
        # override procedure)
        exit(3)
    LoggerHelper.write_info(f"terraform init & plan passed successfully")

    # modified
    tags_templates_creator = OverrideTagsTemplatesCreator(tags_dict, terraform_version)

    all_tf_files = FilesHelper.get_all_files(tfs_folder_path, ".tf")
    all_tf_files_without_overrides = [file for file in all_tf_files if not file.file_name.endswith("_override.tf")]

    untaggable_resources_types = []
    if os.path.exists(exclude_from_tagging_file_path):
        with open(exclude_from_tagging_file_path) as exclude_from_tagging_file:
            untaggable_resources_types = json.load(exclude_from_tagging_file)
        LoggerHelper.write_info(f"User decided to exclude the following resources types from tagging: {untaggable_resources_types}")

    LoggerHelper.write_info("----------------------------------------------------------------------------------------")
    LoggerHelper.write_info(f"Try to create override files to those tf's': {all_tf_files_without_overrides}\n")
    # Create override files to all the tf files that in the main_tf_dir_path
    for file in all_tf_files_without_overrides:
        rt = ResourcesTagger(file, tags_templates_creator)
        rt.create_override_file(untaggable_resources_types)
    LoggerHelper.write_info("----------------------------------------------------------------------------------------")

    LoggerHelper.write_info(f"Trying to preform terraform init & plan in the directory '{tfs_folder_path}'"
                            " in order to check for any untaggable resources in the override files")
    # modified
    # Check (by analyzing the terraform plan output) to see if any of the override files
    # has a "tags/labels" that was assigned to untaggable resources
    stdout, stderr, return_code = _perform_terraform_init_plan(tfs_folder_path, inputs_dict)

    # Analyzing any errors (if exist) from the terraform plan output
    LoggerHelper.write_info(f"Checking for any errors in plan output")
    if stderr:
        LoggerHelper.write_warning("Errors founds in plan output. The errors are:\n\n"
                                   f"{stderr}\n")
        LoggerHelper.write_info("Trying to search for any untaggable resources")
        untaggable_resources_types_from_plan = _get_untaggable_resources_types_from_plan_output(text=stderr)

        # If we found any untaggable resource then we need to create new override files
        # but this time without the untaggable_resources
        if untaggable_resources_types_from_plan:
            LoggerHelper.write_warning(f"The following resources (in the tf files) are untaggable:"
                                       f" {untaggable_resources_types_from_plan}")
            untaggable_resources_types.extend(untaggable_resources_types_from_plan)

            LoggerHelper.write_info(
                "----------------------------------------------------------------------------------------")
            LoggerHelper.write_info(
                f"Creating new override files without the untaggable resources to those tf's': {all_tf_files_without_overrides}\n")
            for file in all_tf_files_without_overrides:
                rt = ResourcesTagger(file, tags_templates_creator)
                # create new override file but this time without the untaggable_resources
                rt.create_override_file(untaggable_resources_types)
            LoggerHelper.write_info(
                "----------------------------------------------------------------------------------------")

            # We need to do one final run of terraform init & plan in order to check that after the creation of the
            # new override files the validation passes.
            # If it's still not pass that we probably did something wrong and we need to exit with error
            LoggerHelper.write_info(f"Trying to preform one final terraform init & plan in the directory '{tfs_folder_path}'"
                " in order to check for any validation errors in the new override files")
            # modified
            stdout, stderr, return_code = _perform_terraform_init_plan(tfs_folder_path, inputs_dict)
            if return_code != 0 or stderr:
                LoggerHelper.write_error("Errors were found in the last validation check:"
                                         f" (Return_code is {return_code})"
                                         f"\n\nErrors are:\n{stderr}\n")
                LoggerHelper.write_error("Tagging terraform resources operation has FAILED !!!!!")
                exit(1)

        else:
            LoggerHelper.write_warning("No untaggable resources were found, but errors in plan file do exists")
            LoggerHelper.write_error("Tagging terraform resources operation has FAILED !!!!!")
            exit(1)
    else:
        LoggerHelper.write_info("No errors founds in plan output")

    LoggerHelper.write_info("Successfully finish creating override files to tf files\n\n\n\n")


def _validate_terraform_version_arg(terraform_version_arg: str) -> bool:
    if not terraform_version_arg:
        return False

    version_arr = terraform_version_arg.split(".")
    if len(version_arr) != 3:
        return False

    return version_arr[0].isdigit() and version_arr[1].isdigit()