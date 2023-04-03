import json
import logging
import os
import re
import shutil
from functools import lru_cache
from subprocess import check_output, STDOUT, CalledProcessError
from typing import Dict
from pathlib import Path

from cloudshell.cp.terraform.handlers.cp_backend_handler import CPBackendHandler
from cloudshell.cp.terraform.handlers.cp_downloader import CPDownloader
from cloudshell.cp.terraform.handlers.provider_handler import CPProviderHandler
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.iac.terraform.constants import ALLOWED_LOGGING_CMDS, \
    OUTPUT, APPLY, PLAN, INIT, DESTROY, ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.exceptions import TerraformExecutionError
from cloudshell.iac.terraform.services.local_dir_service import \
    validate_tf_exe, handle_remove_readonly
from cloudshell.iac.terraform.services.string_cleaner import StringCleaner
from cloudshell.iac.terraform.tagging.tag_terraform_resources import \
    start_tagging_terraform_resources
from cloudshell.iac.terraform.tagging.tags import TagsManager


class CPTfProcExec:
    # def __init__(self, shell_helper: ShellHelperObject, sb_data_handler: SandboxDataHandler,
    #              backend_handler: BackendHandler, input_output_service: InputOutputService):
    #     self._shell_helper = shell_helper
    #     self._sb_data_handler = sb_data_handler
    #     self._backend_handler = backend_handler
    #     self._input_output_service = input_output_service
    #     self._tf_working_dir = sb_data_handler.get_tf_working_dir()
    #
    #     dt = datetime.now().strftime("%d_%m_%y-%H_%M_%S")
    #     self._exec_output_log = _create_logger(
    #         log_group=shell_helper.sandbox_id, log_category="QS", log_file_prefix=f"TF_EXEC_LOG_{dt}"
    #     )

    def __init__(
            self,
            resource_config: TerraformResourceConfig,
            sandbox_id: str,
            logger: logging.Logger,
            backend_handler: CPBackendHandler,
            tag_manager: TagsManager,
    ):
        self._logger = logger
        self._resource_config = resource_config
        self._sandbox_id = sandbox_id
        self._backend_handler = backend_handler
        self._tag_manager = tag_manager
        self._tf_working_dir = None
        self._provider_handler = CPProviderHandler(self._resource_config, self._logger)

    def _get_tf_working_dir(self, deploy_app) -> str:
        if not self._tf_working_dir:
            downloader = CPDownloader(self._resource_config, self._logger)
            tf_working_dir = downloader.download_terraform_module(deploy_app)

            local_tf_exe = self._resource_config.local_terraform

            # if offline, can copy local terraform exe (must exist already on ES)
            if local_tf_exe:
                validate_tf_exe(local_tf_exe)
                self._logger.info(f"Copying Local TF exe: '{local_tf_exe}'")
                shutil.copy(local_tf_exe, tf_working_dir)
            else:
                downloader.download_terraform_executable(tf_working_dir)
            self._tf_working_dir = tf_working_dir

        return self._tf_working_dir

    def delete_local_temp_dir(self, deploy_app: VMFromTerraformGit):
        tf_path = Path(self._get_tf_working_dir(deploy_app))
        tmp_folder_found = False
        while not tmp_folder_found:
            objects_in_folder = os.listdir(tf_path.parent.absolute())
            if len(objects_in_folder) == 2:
                if 'REPO' in objects_in_folder and 'repo.zip' in objects_in_folder:
                    tmp_folder_found = True
            tf_path = Path(tf_path.parent.absolute())
        tf_path_str = str(tf_path)
        shutil.rmtree(tf_path_str, onerror=handle_remove_readonly)

    def init_terraform(self, deploy_app: VMFromTerraformGit, app_name: str):
        self._logger.info("Performing Terraform Init...")
        tf_working_dir = self._get_tf_working_dir(deploy_app)
        self._backend_handler.generate_backend_cfg_file(
            app_name=app_name,
            sandbox_id=self._sandbox_id,
            working_dir=tf_working_dir
        )
        backend_config_vars = self._backend_handler.get_backend_secret_vars()

        variables = ["init", "-no-color"]
        if backend_config_vars:
            for key in backend_config_vars.keys():
                variables.append(f'-backend-config={key}={backend_config_vars[key]}')
        try:
            self._run_tf_proc_with_command(variables, INIT)
        except Exception as e:
            raise

    def destroy_terraform(self, deployed_app: BaseTFDeployedApp):
        self._logger.info("Performing Terraform Destroy")
        cmd = ["destroy", "-auto-approve", "-no-color"]

        tf_vars = deployed_app.terraform_inputs | \
                  deployed_app.terraform_sensitive_inputs

        # add all TF variables to command
        for tf_var_name, tf_var_value in tf_vars.items():
            cmd.append("-var")
            cmd.append(f"{tf_var_name}={tf_var_value}")

        try:
            self._run_tf_proc_with_command(cmd, DESTROY)
            self._backend_handler.delete_backend_tf_state_file(deployed_app.name,
                                                               self._sandbox_id)
        except Exception as e:
            raise

    def tag_terraform(self, deploy_app: VMFromTerraformGit) -> None:
        try:
            apply = self._resource_config.apply_tags
            if not apply:
                self._logger.info("Skipping Adding Tags to Terraform Resources")
                return

            self._logger.info("Adding Tags to Terraform Resources")

            inputs_dict = deploy_app.terraform_inputs | \
                          deploy_app.terraform_sensitive_inputs


            # add all TF variables to command

            # default_tags_dict: dict = self._shell_helper.default_tags.get_default_tags()

            tags_dict = self._resource_config.custom_tags | \
                        deploy_app.custom_tags | self._tag_manager.get_default_tags()

            # if check_tag_input:
            #     custom_tags_inputs = self._input_output_service.get_tags_from_custom_tags_attribute()
            # else:
            #     custom_tags_inputs = {}
            #
            # tags_dict = {**custom_tags_inputs, **default_tags_dict}

            if len(tags_dict) > 50:
                raise ValueError(
                    "AWS and Azure have a limit of 50 tags per resource, you have " + str(
                        len(tags_dict)))

            #self._logger.info(self._tf_working_dir)

            terraform_version = self._resource_config.terraform_version

            start_tagging_terraform_resources(self._get_tf_working_dir(deploy_app),
                                              self._logger,
                                              tags_dict, inputs_dict,
                                              terraform_version)
        except Exception:
            self._logger.error(
                "Failed to apply tags")
            raise

    def plan_terraform(self, deploy_app, vm_name=None) -> None:
        self._logger.info("Running Terraform Plan")

        cmd = ["plan", "-out", "planfile", "-input=false", "-no-color"]
        if vm_name:
            cmd.append("-var")
            cmd.append(f"virtual_machine_name={vm_name}")

        tf_vars = deploy_app.terraform_inputs | \
                  deploy_app.terraform_sensitive_inputs

        # add all TF variables to command
        for tf_var_name, tf_var_value in tf_vars.items():
            cmd.append("-var")
            cmd.append(f"{tf_var_name}={tf_var_value}")

        try:
            self._run_tf_proc_with_command(cmd, PLAN)
        except Exception:
            self._logger.error(
                "Terraform plan failed.")
            raise

    def apply_terraform(self) -> None:
        self._logger.info("Running Terraform Apply")

        cmd = ["apply", "--auto-approve", "-no-color", "planfile"]

        try:
            self._logger.info("Executing Terraform Apply...")
            self._run_tf_proc_with_command(cmd, APPLY)
            self._logger.info("Terraform Apply completed")
        except Exception as e:
            self._logger.info("Terraform Apply Failed")
            raise

    def save_terraform_outputs(self):
        try:
            self._logger.info("Running 'terraform output -json'")

            # get all TF outputs in json format
            cmd = ["output", "-json"]
            tf_exec_output = self._run_tf_proc_with_command(cmd, OUTPUT,
                                                            write_to_log=False)
            unparsed_output_json = json.loads(tf_exec_output)

            self._parse_and_save_outputs(unparsed_output_json)

        except Exception as e:
            self._logger.error(
                f"Error occurred while trying to parse Terraform outputs -> {str(e)}")
            raise

    def _parse_and_save_outputs(self, unparsed_output_json: Dict) -> None:
        """Parse the raw json from "terraform output -json" and update service attributes that are mapped to specific outputs.
        If "Terraform Outputs" attribute exist then save all unmapped outputs on this attribute
        """
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
                pass
                # attr_update_req.append(AttributeNameValue(matched_attr_name,
            # unparsed_output_json[output]['value']))

            if self._is_explicitly_mapped_output(output):
                mapped_attr_name = self._driver_helper.attr_handler.\
                    get_2nd_gen_attribute_full_name(self._outputs_map[output])
                # attr_update_req.append(
                #     AttributeNameValue(mapped_attr_name, unparsed_output_json[output]['value']))

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
            # attr_update_req.append(AttributeNameValue(tf_out_attr, output_string))

        if tf_sensitive_out_attr in self._driver_helper.tf_service.attributes:
            # parse sensitive unmapped outputs
            sensitive_output_string = self._parse_outputs_to_csv(unmaped_sensitive_outputs)
            # prepare update request for sensitive unmapped attributes
            # attr_update_req.append(AttributeNameValue(tf_sensitive_out_attr, sensitive_output_string))

        # send attribute update request using CS API
        # if attr_update_req:
        #     self._driver_helper.api.SetServiceAttributesValues(self._driver_helper.sandbox_id,
        #                                                        self._driver_helper.tf_service.name, attr_update_req)

    # def can_execute_run(self) -> bool:
    #     execute_status = self._sb_data_handler.get_status(EXECUTE_STATUS)
    #     destroy_status = self._sb_data_handler.get_status(DESTROY_STATUS)
    #     if destroy_status in [DESTROY_FAILED] and execute_status == APPLY_PASSED:
    #         return False
    #     return True
    #
    # def can_destroy_run(self) -> bool:
    #     execute_status = self._sb_data_handler.get_status(EXECUTE_STATUS)
    #     if execute_status not in [APPLY_PASSED, APPLY_FAILED]:
    #         return False
    #     return True

    def _run_tf_proc_with_command(self, cmd: list, command: str,
                                  write_to_log: bool = True) -> str:
        tform_command = [f"{os.path.join(self._tf_working_dir, 'terraform.exe')}"]
        tform_command.extend(cmd)

        try:
            output = check_output(tform_command, cwd=self._tf_working_dir,
                                  stderr=STDOUT).decode('utf-8')

            clean_output = StringCleaner.get_clean_string(output)
            self._logger.info(f"{command} - {clean_output}")
            return output

        except CalledProcessError as e:
            clean_output = StringCleaner.get_clean_string(e.output.decode('utf-8'))
            self._logger.error(
                f"Error occurred while trying to execute Terraform | Output = {clean_output}"
            )
            if command in ALLOWED_LOGGING_CMDS:
                self._logger.error(f"{command} - {clean_output}")
            raise TerraformExecutionError(f"Error during Terraform {command}. "
                                          f"For more information please look at the logs.",
                                          clean_output)
        except Exception as e:
            clean_output = StringCleaner.get_clean_string(str(e))
            self._logger.error(f"Error Running Terraform {command} {clean_output}")
            raise TerraformExecutionError(
                "Error during Terraform Plan. For more information please look at the logs.")

    # def _write_to_exec_log(self, command: str, log_data: str, log_level: int) -> None:
    #     clean_output = StringCleaner.get_clean_string(log_data)
    #     self._exec_output_log.log(
    #         log_level,
    #         f"-------------------------------------------------=< {command} START "
    #         f">=-------------------------------------------------\n"
    #     )
    #     self._exec_output_log.log(log_level, clean_output)
    #     self._exec_output_log.log(
    #         log_level,
    #         f"-------------------------------------------------=< {command} END "
    #         f">=---------------------------------------------------\n"
    #     )
    #
    # def _set_service_status(self, status: str, description: str):
    #     self._shell_helper.live_status_updater.set_service_live_status(
    #         self._shell_helper.tf_service.name,
    #         status,
    #         description
    #     )
