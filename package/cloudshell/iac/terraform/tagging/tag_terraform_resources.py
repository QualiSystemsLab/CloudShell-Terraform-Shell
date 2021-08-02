import re
import sys
import traceback
from typing import List
import hcl2
import os
import subprocess
import logging
from inspect import getframeinfo, stack
from functools import wraps
import json


# =====================================================================================================================
from cloudshell.iac.terraform.models.exceptions import TerraformAutoTagsError


class Constants:
    TAGS = "tags"  # used for tag aws and azure resources in terraform
    LABELS = "labels"  # used for tag kubernetes resources in terraform
    # COLONY_VARIABLES_FILE_NAME = "variables.colony.tfvars"
    # COLONY_TAGS_FILE_NAME = "colony_tags.json"
    OVERRIDE_LOG_FILE_NAME = "override_log"
    EXCLUDE_FROM_TAGGING_FILE_NAME = "exclude_from_tagging.json"
    # TERRAFORM_FOLDER_NAME = "terraform"

    # @staticmethod
    # def get_tfs_folder_path(main_folder: str):
    #     return os.path.join(main_folder,
    #                         Constants.TERRAFORM_FOLDER_NAME)

    # @staticmethod
    # def get_colony_tags_path(main_folder: str):
    #     return os.path.join(main_folder,
    #                         Constants.COLONY_TAGS_FILE_NAME)

    @staticmethod
    def get_override_log_path(main_folder: str):
        return os.path.join(main_folder,
                            Constants.OVERRIDE_LOG_FILE_NAME)

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


class LoggerHelper:
    log_instance = None

    @staticmethod
    def init_logging(logger: logging.Logger):
        LoggerHelper.log_instance = logger

    @staticmethod
    def actual_write(log_type: str, logger: logging.Logger, msg: str, code_line: int = None):
        try:
            if code_line is None:
                caller = getframeinfo(stack()[1][0])
                code_line = caller.lineno
            if log_type == "info":
                logger.info(f" Line {code_line}]:  {msg}")
            elif log_type == "warning":
                logger.warning(f" Line {code_line}]:  {msg}")
            elif log_type == "error":
                logger.error(f" Line {code_line}]:  {msg}")
            else:
                raise ValueError('unknown logtype')

        # logging is nice to have but we don't want an error with the log to interfere with the code flow
        except Exception as e:
            print(e)

    @staticmethod
    def write_info(msg: str, code_line: int = None):
        LoggerHelper.actual_write("info", LoggerHelper.log_instance, msg, code_line)

    @staticmethod
    def write_warning(msg: str, code_line: int = None):
        LoggerHelper.actual_write("warning", LoggerHelper.log_instance, msg, code_line)

    @staticmethod
    def write_error(msg: str, code_line: int = None):
        LoggerHelper.actual_write("error", LoggerHelper.log_instance, msg, code_line)

# =====================================================================================================================


def parse_comma_separated_string(params_string: str = None) -> dict:
    res = {}

    if not params_string:
        return res

    key_values = params_string.split(",")

    for item in key_values:
        parts = item.split("=")
        if len(parts) != 2:
            raise ValueError("Line must be comma-separated list of key=values: key1=val1, key2=val2...")

        key = parts[0].strip()
        val = parts[1].strip()

        res[key] = val

    return res


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

@ExceptionWrapper.wrap_class
class OverrideTagsTemplatesCreator:
    def __init__(self, tags_dict: dict):
        # self.colony_tags_file_path = colony_tags_file_path
        self.colony_tags_dict = tags_dict
        self.colony_tags_flat_map = ""  # will be "map(<tag1>,<tag2>,...)"
        self.colony_autoScaling_tags_flat_maps_list = ""  # will be list(<autoScalingTag1>,<autoScalingTag2>....)

        # if os.path.exists(self.colony_tags_file_path):
        #     LoggerHelper.write_info(f"Reading colony tags from \"{self.colony_tags_file_path}\"")
        #     self._read_and_save_tags_from_file()
        # else:
        #     LoggerHelper.write_error(f"\"{self.colony_tags_file_path}\" does not exists")
        #     LoggerHelper.write_error(f"Could not find colony tags file, exit the tagging process")
        #     exit(1)

        LoggerHelper.write_info(f"Initiate default tags templates")
        self._init_colony_tags_flat_map()
        self._init_colony_autoScaling_tags_flat_maps_list()

    # def _read_and_save_tags_from_file(self):
    #     with open(self.colony_tags_file_path) as tags_file:
    #         tags = json.load(tags_file)
    #         for k, v in tags.items():
    #             self.colony_tags_dict[k] = v

    def _init_colony_tags_flat_map(self):
        colony_tags_to_list = []
        for key, value in self.colony_tags_dict.items():
            colony_tags_to_list.append(f"\"{key}\",\"{value}\"")

        if not colony_tags_to_list:
            return
        map_value = " , ".join(colony_tags_to_list)
        self.colony_tags_flat_map = f"map({map_value})"

    def _init_colony_autoScaling_tags_flat_maps_list(self):
        colony_tags_to_list = []
        for key, value in self.colony_tags_dict.items():
            colony_tags_to_list.append(f"map(\"key\",\"{key}\",\"value\",\"{value}\",\"propagate_at_launch\",\"true\")")

        if not colony_tags_to_list:
            return

        # All the \t and \n in here is just so that the override will look good and readable
        # (in case we need to look at it)
        list_of_maps_value = " ,\n\t\t".join(colony_tags_to_list)
        self.colony_autoScaling_tags_flat_maps_list = f"\nlist(\n\t\t{list_of_maps_value}\n)"

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
        if not self.colony_tags_flat_map:
            return ""

        separator = ", " if not client_str_tags.replace(" ", "").endswith(",") else " "

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=f"\"${{merge({client_str_tags}{separator}{self.colony_tags_flat_map})}}\"")

    def get_concat_tags_template(self, resource_type: str, resource_name: str, client_str_tags: str) -> str:
        if not self.colony_autoScaling_tags_flat_maps_list:
            return ""

        separator = ", " if not client_str_tags.replace(" ", "").endswith(",") else " "

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=f"\"${{concat({client_str_tags}{separator}{self.colony_autoScaling_tags_flat_maps_list})}}\"")

    def get_colony_tags_with_client_dict_tags_template(self, resource_type: str, resource_name: str, client_dict_tags: dict) -> str:
        tags = {} if not client_dict_tags else client_dict_tags
        # To add out tags to the client dict tags AND to OVERRIDE them in case we have the same tag names
        for key, value in self.colony_tags_dict.items():
            tags[key] = value

        all_tags_in_str_list = []
        for key, value in tags.items():
            all_tags_in_str_list.append(f"{key} = \"{value}\"")

        if not all_tags_in_str_list:
            return ""

        all_tags_as_str = ", ".join(all_tags_in_str_list)
        all_tags_as_str = f"{{{all_tags_as_str}}}"

        return self._get_basic_override_tags_template(resource_type=resource_type,
                                                      resource_name=resource_name,
                                                      tags=all_tags_as_str)

    def get_colony_tags_with_autoscaling_client_dict_tags_template(self, resource_type: str, resource_name: str, client_list_dict_tags: list) -> str:
        list_of_tags_dict = [] if not client_list_dict_tags else client_list_dict_tags
        for key, value in self.colony_tags_dict.items():
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

@ExceptionWrapper.wrap_class
class Hcl2Parser:
    @staticmethod
    def get_tf_file_as_dict(tf_file_path: str) -> dict:
        with(open(tf_file_path, 'r')) as client_tf_file:
            return hcl2.load(client_tf_file)

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

        # When hcl2 parse a tf file it return all the tags blocks in a resource .
        # But a valid tf file (according to terraform) allow only one tags block in a resource.
        # So even if the hcl2 will return many tags blocks we will only be working with the first of them.
        # But because we run 'terraform init' and 'terraform plan' before we run this py file
        # we can be sure that if we have a tags block in the resource then we have only one
        # (because otherwise 'terraform plan' command would have return an error)
        if tags:
            # we replace ' with " becuase hc2l has some bug:
            #  for example it parse --> merge(local.common_tags, {"Name"="tomer"})
            # to --> merge(local.common_tags, {'Name'='tomer'})  and this is invalid syntax according to terraform
            if type(tags[0]) is str:
                tags = tags[0].replace("'", "\"").replace(",,", ",")  # due to bug in hcl2 library
            else:
                tags = tags[0]

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

    def _get_colony_tags_with_client_string_tags(self, terraform_resource: TerraformResource) -> str:
        client_tags = terraform_resource.tags.replace("\n", "")

        # It's important that we search for MERGED_TAGS_PATTERN before we search for SINGLE_VAR_PATTERN because
        # the MERGED_TAGS_PATTERN can also be recognized as a SINGLE_VAR_PATTERN but we want to act differently if it is
        # MERGED_TAGS_PATTERN
        parsed_client_tags = RegexHelper.get_single_group_match_from_regex_result(text=client_tags,
                                                                                  pattern=RegexHelper.MERGED_TAGS_PATTERN)
        if not parsed_client_tags:  # if not find concat pattern then try to fall back to single var pattern
            parsed_client_tags = RegexHelper.get_single_group_match_from_regex_result(text=client_tags,
                                                                                      pattern=RegexHelper.SINGLE_VAR_PATTERN)

        # If succeed to find any pattern then create a new merge tags template
        if parsed_client_tags:
            return self.tags_creator.get_merge_tags_template(
                resource_type=terraform_resource.resource_type,
                resource_name=terraform_resource.resource_name,
                client_str_tags=parsed_client_tags)

        else:  # Otherwise raise an error
            raise Exception("Unable to process client tags")

    def _get_colony_tags_with_autoscaling_client_string_tags(self, terraform_resource: TerraformResource) -> str:
        client_tags = terraform_resource.tags.replace("\n", "")
        # Try at first to find a concat pattern.
        # It's important that we search for CONCAT_LIST_TAGS_PATTERN before we search for SINGLE_VAR_PATTERN because
        # the CONCAT_LIST_TAGS_PATTERN can also be recognized as a SINGLE_VAR_PATTERN but we want to act differently
        # if it is CONCAT_LIST_TAGS_PATTERN
        parsed_client_tags = RegexHelper.get_single_group_match_from_regex_result(text=client_tags,
                                                                                  pattern=RegexHelper.CONCAT_LIST_TAGS_PATTERN)
        if not parsed_client_tags:  # if not find concat pattern then try to fall back to single var pattern
            parsed_client_tags = RegexHelper.get_single_group_match_from_regex_result(text=client_tags,
                                                                                      pattern=RegexHelper.SINGLE_VAR_PATTERN)
        # If succeed to find any pattern then create a new concat tags template
        if parsed_client_tags:
            return self.tags_creator.get_concat_tags_template(
                resource_type=terraform_resource.resource_type,
                resource_name=terraform_resource.resource_name,
                client_str_tags=parsed_client_tags)
        else:  # Otherwise raise an error
            raise Exception("Unable to process client tags")

    def _get_colony_tags_with_client_dict_tags(self, terraform_resource: TerraformResource) -> str:
        return self.tags_creator.get_colony_tags_with_client_dict_tags_template(
            resource_type=terraform_resource.resource_type,
            resource_name=terraform_resource.resource_name,
            client_dict_tags=terraform_resource.tags)

    def _get_colony_tags_with_autoscaling_client_dict_tags(self, terraform_resource: TerraformResource) -> str:
        return self.tags_creator.get_colony_tags_with_autoscaling_client_dict_tags_template(
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
                        self._get_colony_tags_with_autoscaling_client_dict_tags(terraform_resource))
                # i.e tags is most likely = "${concat(<List_of_maps1>,<List_of_maps2>,....)}" or "${<List_of_maps>}"
                elif type(terraform_resource.tags) is str:
                    override_file_stream.write(
                        self._get_colony_tags_with_autoscaling_client_string_tags(terraform_resource))
            else:
                # if we don't have tags or the tags are dict like "  key1="value1" , key2="value2"  "
                if not terraform_resource.tags or type(terraform_resource.tags) is dict:
                    override_file_stream.write(self._get_colony_tags_with_client_dict_tags(terraform_resource))
                # i.e tags is most likely = "${merge(<map1>,<map2>,....)}" or "${<map>}"
                elif type(terraform_resource.tags) is str:
                    override_file_stream.write(self._get_colony_tags_with_client_string_tags(terraform_resource))

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


def _perform_terraform_init_plan(main_tf_dir_path: str, inputs_dict: dict):
    # plan_var_file_command = ""
    # if os.path.exists(os.path.join(main_tf_dir_path, Constants.COLONY_VARIABLES_FILE_NAME)):
    #     plan_var_file_command = f"-var-file={Constants.COLONY_VARIABLES_FILE_NAME}"

    inputs = []

    for inputkey, inputvalue in inputs_dict.items():
        inputs.extend(['-var', f'{inputkey}={inputvalue}'])

    executable_cmd = f'{os.path.join(main_tf_dir_path, "terraform.exe")}'
    init_command = [executable_cmd, 'init', '-no-color']
    plan_command = [executable_cmd, 'plan', '-no-color', '-input=false']
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


def start_tagging_terraform_resources(main_dir_path: str, logger, tags_dict: dict, inputs_dict: dict = dict()):
    if not os.path.exists(main_dir_path):
        raise TerraformAutoTagsError(f"Path {main_dir_path} does not exist")
    tfs_folder_path = main_dir_path
    # log_path = Constants.get_override_log_path(main_dir_path)
    # colony_tags_file_path = Constants.get_colony_tags_path(main_dir_path)
    exclude_from_tagging_file_path = Constants.get_exclude_from_tagging_file_path(main_dir_path)

    LoggerHelper.init_logging(logger)

    LoggerHelper.write_info(f"Trying to preform terraform init & plan in the directory '{tfs_folder_path}'"
                            " in order to check for any validation errors in tf files")
    stdout, stderr, return_code = _perform_terraform_init_plan(tfs_folder_path, inputs_dict)
    if return_code != 0 or stderr:
        LoggerHelper.write_error("Exit before the override procedure began because the init/plan failed."
                                 f" (Return_code is {return_code})"
                                 f"\n\nErrors are:\n{stderr}\n")
        # Error Code 3 mark to the outside tf script (that run me) that there was an error but not because of
        # the override procedure (but because the client tf file has compile errors even before we started the
        # override procedure)

        # Had to change exit(3) to "raise" so exception can be handled outside
        #exit(3)
        raise TerraformAutoTagsError("Validation errors during Terraform Init/Plan when applying automated tags")
    LoggerHelper.write_info(f"terraform init & plan passed successfully")

    tags_templates_creator = OverrideTagsTemplatesCreator(tags_dict)

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

            stdout, stderr, return_code = _perform_terraform_init_plan(tfs_folder_path, inputs_dict)
            if return_code != 0 or stderr:
                LoggerHelper.write_error("Errors were found in the last validation check:"
                                         f" (Return_code is {return_code})"
                                         f"\n\nErrors are:\n{stderr}\n")
                LoggerHelper.write_error("Tagging terraform resources operation has FAILED !!!!!")
                # Had to change exit(1) to "raise" so exception can be handled outside
                # exit(1)
                raise TerraformAutoTagsError("Validation errors during Terraform Init/Plan "
                                             "when applying automated tags")

        else:
            LoggerHelper.write_warning("No untaggable resources were found, but errors in plan file do exists")
            LoggerHelper.write_error("Tagging terraform resources operation has FAILED !!!!!")
            # Had to change exit(1) to "raise" so exception can be handled outside
            # exit(1)
            raise TerraformAutoTagsError("No untaggable resources were found, but there is an error in Terraform "
                                         "Plan when applying automated tags. Please check the logs for more details")
    else:
        LoggerHelper.write_info("No errors founds in plan output")

    LoggerHelper.write_info("Successfully finish creating override files to tf files\n\n\n\n")
