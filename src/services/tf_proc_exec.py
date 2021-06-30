from datetime import datetime
import json
import os

from subprocess import check_output, STDOUT, CalledProcessError

from cloudshell.api.cloudshell_api import AttributeNameValue
from cloudshell.logging.qs_logger import _create_logger

from constants import ERROR_LOG_LEVEL, INFO_LOG_LEVEL, EXECUTE_STATUS, APPLY_PASSED, PLAN_FAILED, INIT_FAILED, \
    DESTROY_STATUS, DESTROY_FAILED, APPLY_FAILED, DESTROY_PASSED
from driver_helper_obj import DriverHelperObject
from models.exceptions import TerraformExecutionError
from services.sb_data_handler import SbDataHandler
from services.string_cleaner import StringCleaner


class TfProcExec(object):
    def __init__(self, driver_helper_obj: DriverHelperObject, sb_data_handler: SbDataHandler):
        self._driver_helper_obj = driver_helper_obj
        self._tf_workingdir = sb_data_handler.get_tf_working_dir()
        self._sb_data_handler = sb_data_handler

        dt = datetime.now().strftime("%d_%m_%y-%H_%M_%S")
        self._exec_output_log = _create_logger(
            log_group=driver_helper_obj.res_id, log_category="QS", log_file_prefix=f"TF_EXEC_LOG_{dt}"
        )

    def init_terraform(self):
        self._driver_helper_obj.logger.info("Performing Terraform Init")
        self._driver_helper_obj.api.WriteMessageToReservationOutput(self._driver_helper_obj.res_id,
                                                                    "Performing Terraform Init...")
        vars = ["init", "-no-color"]
        try:
            self._run_tf_proc_with_command(vars, "INIT")
        except Exception as e:
            self._sb_data_handler.set_status(EXECUTE_STATUS, INIT_FAILED)
            # self._driver_helper_obj.api.SetServiceLiveStatus()
            raise

    def destroy_terraform(self):
        self._driver_helper_obj.logger.info("Performing Terraform Destroy")
        self._driver_helper_obj.api.WriteMessageToReservationOutput(self._driver_helper_obj.res_id,
                                                                    "Performing Terraform Destroy...")
        vars = ["destroy"]
        if self._driver_helper_obj.tf_service.terraform_inputs:
            for input in self._driver_helper_obj.tf_service.terraform_inputs.split(","):
                vars.append("-var")
                vars.append(f'{input}')
        for var in ["-auto-approve", "-no-color"]:
            vars.append(var)
        try:
            self._run_tf_proc_with_command(vars, "DESTROY")
            self._sb_data_handler.set_status(DESTROY_STATUS, DESTROY_PASSED)
        except Exception as e:
            self._sb_data_handler.set_status(DESTROY_STATUS, DESTROY_FAILED)
            raise

    def plan_terraform(self) -> None:
        self._driver_helper_obj.logger.info("Running Terraform Plan")
        self._driver_helper_obj.api.WriteMessageToReservationOutput(self._driver_helper_obj.res_id,
                                                                    "Generating Terraform Plan...")
        vars = ["plan"]
        if self._driver_helper_obj.tf_service.terraform_inputs:
            for input in self._driver_helper_obj.tf_service.terraform_inputs.split(","):
                vars.append("-var")
                vars.append(f'{input}')
        for var in ["-out", "planfile"]:
            vars.append(var)
        try:
            self._run_tf_proc_with_command(vars, "PLAN")
        except Exception as e:
            self._sb_data_handler.set_status(EXECUTE_STATUS, PLAN_FAILED)
            raise

    def apply_terraform(self):
        self._driver_helper_obj.logger.info("Running Terraform Apply")
        self._driver_helper_obj.api.WriteMessageToReservationOutput(self._driver_helper_obj.res_id,
                                                                    "Executing Terraform Apply with auto approve...")
        vars = ["apply", "--auto-approve", "-no-color", "planfile"]

        try:
            self._run_tf_proc_with_command(vars, "APPLY")
            self._sb_data_handler.set_status(EXECUTE_STATUS, APPLY_PASSED)
        except Exception as e:
            self._sb_data_handler.set_status(EXECUTE_STATUS, APPLY_FAILED)
            raise

    def parse_and_save_terraform_outputs(self):
        try:
            self._driver_helper_obj.logger.info("Running 'terraform output -json'")
            vars = ["output", "-json"]
            tf_exec_output = self._run_tf_proc_with_command(vars, "OUTPUT")

            unparsed_output_json = json.loads(tf_exec_output)
            output_string = []

            for output in unparsed_output_json:
                output_string += [(output + '=' + str(unparsed_output_json[output]['value']))]

            attr_name = f"{self._driver_helper_obj.tf_service.cloudshell_model_name}.Terraform Output"
            attr_req = [AttributeNameValue(attr_name, ",".join(output_string))]
            self._driver_helper_obj.api.SetServiceAttributesValues(self._driver_helper_obj.res_id,
                                                                   self._driver_helper_obj.tf_service.name, attr_req)
        except Exception as e:
            self._driver_helper_obj.logger.error(f"Error occurred while trying to parse Terraform outputs -> {str(e)}")
            raise

    def can_execute_run(self) -> bool:
        execute_status = self._sb_data_handler.get_status(EXECUTE_STATUS)
        destroy_status = self._sb_data_handler.get_status(DESTROY_STATUS)
        if execute_status in [APPLY_FAILED]:
            return False
        if destroy_status in [DESTROY_FAILED] and execute_status == APPLY_PASSED:
            return False
        return True

    def can_destroy_run(self) -> bool:
        execute_status = self._sb_data_handler.get_status(EXECUTE_STATUS)
        if execute_status not in [APPLY_PASSED, APPLY_FAILED]:
            return False
        return True

    def _run_tf_proc_with_command(self, vars: list, command: str) -> str:
        tform_command = [f"{os.path.join(self._tf_workingdir,'terraform.exe')}"]
        tform_command.extend(vars)

        try:
            output = check_output(tform_command, cwd=self._tf_workingdir, stderr=STDOUT).decode('utf-8')

            clean_output = StringCleaner.get_clean_string(output)
            self._write_to_to_exec_log(command, clean_output, INFO_LOG_LEVEL)
            return output

        except CalledProcessError as e:
            clean_output = StringCleaner.get_clean_string(e.output.decode('utf-8'))
            self._driver_helper_obj.logger.error(
                f"Error occurred while trying to execute Terraform | Output = {clean_output}"
            )
            self._write_to_to_exec_log(command, clean_output, ERROR_LOG_LEVEL)
            raise TerraformExecutionError("Error during Terraform Plan. For more information please look at the logs.",
                                          clean_output)
        except Exception as e:
            clean_output = StringCleaner.get_clean_string(str(e))
            self._driver_helper_obj.logger.error(f"Error Running Terraform plan {clean_output}")
            raise TerraformExecutionError("Error during Terraform Plan. For more information please look at the logs.")

    def _write_to_to_exec_log(self, command: str, log_data: str, log_level: int) -> None:
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
