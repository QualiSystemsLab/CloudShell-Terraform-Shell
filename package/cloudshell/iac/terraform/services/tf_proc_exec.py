import json
import os
from datetime import datetime
from distutils.util import strtobool
from subprocess import check_output, STDOUT, CalledProcessError
from cloudshell.logging.qs_logger import _create_logger

from cloudshell.iac.terraform.constants import ERROR_LOG_LEVEL, INFO_LOG_LEVEL, EXECUTE_STATUS, APPLY_PASSED, \
    PLAN_FAILED, INIT_FAILED, \
    DESTROY_STATUS, DESTROY_FAILED, APPLY_FAILED, DESTROY_PASSED, INIT, DESTROY, PLAN, OUTPUT, APPLY, \
    ALLOWED_LOGGING_CMDS, ATTRIBUTE_NAMES
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.models.exceptions import TerraformExecutionError
from cloudshell.iac.terraform.services.backend_handler import BackendHandler
from cloudshell.iac.terraform.services.input_output_service import InputOutputService
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler
from cloudshell.iac.terraform.services.string_cleaner import StringCleaner
from cloudshell.iac.terraform.tagging.tag_terraform_resources import start_tagging_terraform_resources


class TfProcExec(object):
    def __init__(self, shell_helper: ShellHelperObject, sb_data_handler: SandboxDataHandler,
                 backend_handler: BackendHandler, input_output_service: InputOutputService):
        self._shell_helper = shell_helper
        self._sb_data_handler = sb_data_handler
        self._backend_handler = backend_handler
        self._input_output_service = input_output_service
        self._tf_working_dir = sb_data_handler.get_tf_working_dir()

        dt = datetime.now().strftime("%d_%m_%y-%H_%M_%S")
        self._exec_output_log = _create_logger(
            log_group=shell_helper.sandbox_id, log_category="QS", log_file_prefix=f"TF_EXEC_LOG_{dt}"
        )

    def init_terraform(self):
        self._shell_helper.logger.info("Performing Terraform Init...")
        self._shell_helper.sandbox_messages.write_message("Running Terraform Init...")

        self._backend_handler.generate_backend_cfg_file()
        backend_config_vars = self._backend_handler.get_backend_secret_vars()

        vars = ["init", "-no-color"]
        if backend_config_vars:
            for key in backend_config_vars.keys():
                vars.append(f'-backend-config={key}={backend_config_vars[key]}')
        try:
            self._set_service_status("Progress 10", "Executing Terraform Init...")
            self._run_tf_proc_with_command(vars, INIT)
            self._set_service_status("Progress 20", "Init Passed")
        except Exception as e:
            self._set_service_status("Offline", "Init Failed")
            self._sb_data_handler.set_status(EXECUTE_STATUS, INIT_FAILED)
            self._shell_helper.sandbox_messages.write_error_message("Init Failed")
            raise

    def destroy_terraform(self):
        self._shell_helper.logger.info("Performing Terraform Destroy")
        self._shell_helper.sandbox_messages.write_message("running Terraform Destroy...")
        cmd = ["destroy", "-auto-approve", "-no-color"]

        tf_vars = self._input_output_service.get_all_terrafrom_variables()

        # add all TF variables to command
        for tf_var in tf_vars:
            cmd.append("-var")
            cmd.append(f"{tf_var.name}={tf_var.value}")

        try:
            self._set_service_status("Progress 50", "Executing Terraform Destroy...")
            self._run_tf_proc_with_command(cmd, DESTROY)
            self._sb_data_handler.set_status(DESTROY_STATUS, DESTROY_PASSED)
            self._set_service_status("Offline", "Destroy Passed")
            self._backend_handler.delete_backend_tf_state_file()
            self._shell_helper.sandbox_messages.write_message("Terraform Destroy completed")

        except Exception as e:
            self._set_service_status("Offline", "Destroy Failed")
            self._sb_data_handler.set_status(DESTROY_STATUS, DESTROY_FAILED)
            self._shell_helper.sandbox_messages.write_error_message("Destroy Failed")
            raise

    def tag_terraform(self) -> None:
        try:
            self._set_service_status("Progress 30", "Applying tags...")
            apply = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.APPLY_TAGS)
            if apply and not strtobool(apply):
                self._shell_helper.logger.info("Skipping Adding Tags to Terraform Resources")
                self._shell_helper.sandbox_messages.write_message("skipping adding tags...")
                return

            self._shell_helper.logger.info("Adding Tags to Terraform Resources")
            self._shell_helper.sandbox_messages.write_message("generating tags...")

            tf_vars = self._input_output_service.get_all_terrafrom_variables()

            inputs_dict = dict()

            # add all TF variables to command
            for tf_var in tf_vars:
                inputs_dict[tf_var.name] = tf_var.value

            default_tags_dict: dict = self._shell_helper.default_tags.get_default_tags()

            check_tag_input = self._shell_helper.attr_handler.get_attribute(ATTRIBUTE_NAMES.CT_INPUTS)
            if check_tag_input:
                custom_tags_inputs = self._input_output_service.get_tags_from_custom_tags_attribute()
            else:
                custom_tags_inputs = {}

            tags_dict = {**custom_tags_inputs, **default_tags_dict}

            if len(tags_dict) > 50:
                raise ValueError("AWS and Azure have a limit of 50 tags per resource, you have " + str(len(tags_dict)))

            self._shell_helper.logger.info(self._tf_working_dir)
            self._shell_helper.logger.info(tags_dict)

            start_tagging_terraform_resources(self._tf_working_dir, self._shell_helper.logger, tags_dict, inputs_dict)
            self._set_service_status("Progress 40", "Tagging Passed")
        except Exception:
            self._set_service_status("Offline", "Tagging Failed")
            self._shell_helper.sandbox_messages.write_error_message("Failed to apply tags")
            raise

    def plan_terraform(self) -> None:
        self._shell_helper.logger.info("Running Terraform Plan")
        self._shell_helper.sandbox_messages.write_message("generating Terraform Plan...")

        cmd = ["plan", "-out", "planfile", "-input=false", "-no-color"]

        tf_vars = self._input_output_service.get_all_terrafrom_variables()

        # add all TF variables to command
        for tf_var in tf_vars:
            cmd.append("-var")
            cmd.append(f"{tf_var.name}={tf_var.value}")

        try:
            self._set_service_status("Progress 50", "Executing Terraform Plan...")
            self._run_tf_proc_with_command(cmd, PLAN)
            self._set_service_status("Progress 60", "Plan Passed")
        except Exception:
            self._set_service_status("Offline", "Plan Failed")
            self._sb_data_handler.set_status(EXECUTE_STATUS, PLAN_FAILED)
            self._shell_helper.sandbox_messages.write_error_message("Plan Failed")
            raise

    def apply_terraform(self):
        self._shell_helper.logger.info("Running Terraform Apply")
        self._shell_helper.sandbox_messages.write_message("executing Terraform Apply...")
        cmd = ["apply", "--auto-approve", "-no-color", "planfile"]

        try:
            self._set_service_status("Progress 70", "Executing Terraform Apply...")
            self._run_tf_proc_with_command(cmd, APPLY)
            self._sb_data_handler.set_status(EXECUTE_STATUS, APPLY_PASSED)
            self._set_service_status("Online", "Apply Passed")
            self._shell_helper.sandbox_messages.write_message("Terraform Apply completed")
        except Exception as e:
            self._set_service_status("Offline", "Apply Failed")
            self._sb_data_handler.set_status(EXECUTE_STATUS, APPLY_FAILED)
            self._shell_helper.sandbox_messages.write_error_message("Apply Failed")
            raise

    def save_terraform_outputs(self):
        try:
            self._shell_helper.logger.info("Running 'terraform output -json'")

            # get all TF outputs in json format
            cmd = ["output", "-json"]
            tf_exec_output = self._run_tf_proc_with_command(cmd, OUTPUT, write_to_log=False)
            unparsed_output_json = json.loads(tf_exec_output)

            self._input_output_service.parse_and_save_outputs(unparsed_output_json)

        except Exception as e:
            self._shell_helper.logger.error(f"Error occurred while trying to parse Terraform outputs -> {str(e)}")
            raise

    def can_execute_run(self) -> bool:
        execute_status = self._sb_data_handler.get_status(EXECUTE_STATUS)
        destroy_status = self._sb_data_handler.get_status(DESTROY_STATUS)
        if destroy_status in [DESTROY_FAILED] and execute_status == APPLY_PASSED:
            return False
        return True

    def can_destroy_run(self) -> bool:
        execute_status = self._sb_data_handler.get_status(EXECUTE_STATUS)
        if execute_status not in [APPLY_PASSED, APPLY_FAILED]:
            return False
        return True

    def _run_tf_proc_with_command(self, cmd: list, command: str, write_to_log: bool = True) -> str:
        tform_command = [f"{os.path.join(self._tf_working_dir, 'terraform.exe')}"]
        tform_command.extend(cmd)

        try:
            output = check_output(tform_command, cwd=self._tf_working_dir, stderr=STDOUT).decode('utf-8')

            clean_output = StringCleaner.get_clean_string(output)
            if write_to_log:
                self._write_to_exec_log(command, clean_output, INFO_LOG_LEVEL)
            return output

        except CalledProcessError as e:
            clean_output = StringCleaner.get_clean_string(e.output.decode('utf-8'))
            self._shell_helper.logger.error(
                f"Error occurred while trying to execute Terraform | Output = {clean_output}"
            )
            if command in ALLOWED_LOGGING_CMDS:
                self._write_to_exec_log(command, clean_output, ERROR_LOG_LEVEL)
            raise TerraformExecutionError(f"Error during Terraform {command}. "
                                          f"For more information please look at the logs.",
                                          clean_output)
        except Exception as e:
            clean_output = StringCleaner.get_clean_string(str(e))
            self._shell_helper.logger.error(f"Error Running Terraform {command} {clean_output}")
            raise TerraformExecutionError("Error during Terraform Plan. For more information please look at the logs.")

    def _write_to_exec_log(self, command: str, log_data: str, log_level: int) -> None:
        clean_output = StringCleaner.get_clean_string(log_data)
        self._exec_output_log.log(
            log_level,
            f"-------------------------------------------------=< {command} START "
            f">=-------------------------------------------------\n"
        )
        self._exec_output_log.log(log_level, clean_output)
        self._exec_output_log.log(
            log_level,
            f"-------------------------------------------------=< {command} END "
            f">=---------------------------------------------------\n"
        )

    def _set_service_status(self, status: str, description: str):
        self._shell_helper.live_status_updater.set_service_live_status(
            self._shell_helper.tf_service.name,
            status,
            description
        )
