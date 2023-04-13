from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output

from cloudshell.cp.terraform.constants import REFRESH
from cloudshell.cp.terraform.handlers.cp_backend_handler import CPBackendHandler
from cloudshell.cp.terraform.handlers.cp_downloader import CPDownloader
from cloudshell.cp.terraform.handlers.provider_handler import CPProviderHandler
from cloudshell.cp.terraform.models.deploy_app import VMFromTerraformGit
from cloudshell.cp.terraform.models.deployed_app import BaseTFDeployedApp
from cloudshell.cp.terraform.models.tf_deploy_result import TFDeployResult
from cloudshell.cp.terraform.resource_config import TerraformResourceConfig
from cloudshell.iac.terraform.constants import (
    ALLOWED_LOGGING_CMDS,
    APPLY,
    DESTROY,
    INIT,
    OUTPUT,
    PLAN,
)
from cloudshell.iac.terraform.models.exceptions import TerraformExecutionError
from cloudshell.iac.terraform.services.local_dir_service import (
    handle_remove_readonly,
    validate_tf_exe,
)
from cloudshell.iac.terraform.services.string_cleaner import StringCleaner
from cloudshell.iac.terraform.tagging.tag_terraform_resources import (
    start_tagging_terraform_resources,
)


class CPTfProcExec:
    def __init__(
        self,
        resource_config: TerraformResourceConfig,
        sandbox_id: str,
        logger: logging.Logger,
        backend_handler: CPBackendHandler,
    ):
        self._logger = logger
        self._resource_config = resource_config
        self._sandbox_id = sandbox_id
        self._backend_handler = backend_handler
        self._tf_working_dir = None
        self._provider_handler = CPProviderHandler(self._resource_config, self._logger)

    def _get_inputs(
        self, deploy_app: VMFromTerraformGit | BaseTFDeployedApp
    ) -> dict[str, str]:
        inputs = (
            deploy_app.terraform_inputs
            | deploy_app.terraform_sensitive_inputs
            | deploy_app.get_app_inputs()
        )

        return inputs

    def set_tf_working_dir(self, tf_working_dir: str):
        self._tf_working_dir = tf_working_dir

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
                if "REPO" in objects_in_folder and "repo.zip" in objects_in_folder:
                    tmp_folder_found = True
            tf_path = Path(tf_path.parent.absolute())
        tf_path_str = str(tf_path)
        shutil.rmtree(tf_path_str, onerror=handle_remove_readonly)

    def init_terraform(self,
                       deploy_app: VMFromTerraformGit | BaseTFDeployedApp,
                       app_name: str):
        self._logger.info("Performing Terraform Init...")
        tf_working_dir = self._get_tf_working_dir(deploy_app)
        self._backend_handler.generate_backend_cfg_file(
            app_name=app_name, sandbox_id=self._sandbox_id, working_dir=tf_working_dir
        )
        backend_config_vars = self._backend_handler.get_backend_secret_vars()

        variables = ["init", "-no-color"]
        if backend_config_vars:
            for key in backend_config_vars.keys():
                variables.append(f"-backend-config={key}={backend_config_vars[key]}")
        try:
            self._run_tf_proc_with_command(variables, INIT)
        except Exception as e:
            raise

    def destroy_terraform(self, deployed_app: BaseTFDeployedApp):
        self._logger.info("Performing Terraform Destroy")
        cmd = ["destroy", "-auto-approve", "-no-color"]

        tf_vars = self._get_inputs(deployed_app)

        # add all TF variables to command
        for tf_var_name, tf_var_value in tf_vars.items():
            cmd.append("-var")
            cmd.append(f"{tf_var_name}={tf_var_value}")

        try:
            self._run_tf_proc_with_command(cmd, DESTROY)
            self._backend_handler.delete_backend_tf_state_file(
                deployed_app.name, self._sandbox_id
            )
        except Exception as e:
            raise

    def tag_terraform(self, deploy_app: VMFromTerraformGit) -> None:
        if self._resource_config.apply_tags:
            try:
                self._logger.info("Adding Tags to Terraform Resources")

                inputs_dict = self._get_inputs(deploy_app)

                tags_dict = (
                    self._resource_config.tags
                    | deploy_app.custom_tags
                )

                if len(tags_dict) > 50:
                    raise ValueError(
                        f"AWS and Azure have a limit of 50 tags per resource, "
                        f"you have {len(tags_dict)}"
                    )

                terraform_version = self._resource_config.terraform_version

                start_tagging_terraform_resources(
                    self._get_tf_working_dir(deploy_app),
                    self._logger,
                    tags_dict,
                    inputs_dict,
                    terraform_version,
                )
            except Exception:
                self._logger.error("Failed to apply tags")
                raise
        else:
            self._logger.info("Skipping Adding Tags to Terraform Resources")

    def plan_terraform(self, deploy_app, vm_name=None) -> None:
        self._logger.info("Running Terraform Plan")

        cmd = ["plan", "-out", "planfile", "-input=false", "-no-color"]
        if vm_name:
            cmd.extend(["-var", f"virtual_machine_name={vm_name}"])

        tf_vars = self._get_inputs(deploy_app)

        # add all TF variables to command
        for tf_var_name, tf_var_value in tf_vars.items():
            cmd.extend(["-var", f"{tf_var_name}={tf_var_value}"])

        try:
            self._run_tf_proc_with_command(cmd, PLAN)
        except Exception:
            self._logger.error("Terraform Plan failed.")
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

    def refresh_terraform(self, deployed_app: BaseTFDeployedApp) -> None:
        self._logger.info("Running Terraform Refresh")

        cmd = ["refresh", "-no-color"]
        tf_vars = self._get_inputs(deployed_app)

        # add all TF variables to command
        for tf_var_name, tf_var_value in tf_vars.items():
            cmd.extend(["-var", f"{tf_var_name}={tf_var_value}"])

        try:
            self._logger.info("Executing Terraform Refresh...")
            self._run_tf_proc_with_command(cmd, REFRESH)
            self._logger.info("Terraform Refresh completed")
        except Exception as e:
            self._logger.info("Terraform Refresh Failed")
            raise

    def save_terraform_outputs(
        self,
            deploy_app: VMFromTerraformGit | BaseTFDeployedApp,
            app_name: str
    ) -> TFDeployResult | None:
        try:
            self._logger.info("Running 'terraform output -json'")

            # get all TF outputs in json format
            cmd = ["output", "-json"]
            tf_exec_output = self._run_tf_proc_with_command(cmd, OUTPUT)
            unparsed_output_json = json.loads(tf_exec_output)

            return TFDeployResult(
                unparsed_output_json=unparsed_output_json,
                deploy_app=deploy_app,
                app_name=app_name,
                path=self._tf_working_dir,
                logger=self._logger,
            )

        except Exception as e:
            self._logger.error(
                f"Error occurred while trying to parse Terraform outputs -> {str(e)}"
            )
            raise

    def _run_tf_proc_with_command(self, cmd: list, command: str) -> str:
        tform_command = [f"{os.path.join(self._tf_working_dir, 'terraform.exe')}"]
        tform_command.extend(cmd)

        try:
            output = check_output(
                tform_command, cwd=self._tf_working_dir, stderr=STDOUT
            ).decode("utf-8")

            clean_output = StringCleaner.get_clean_string(output)
            self._logger.info(f"{command} - {clean_output}")
            return output

        except CalledProcessError as e:
            clean_output = StringCleaner.get_clean_string(e.output.decode("utf-8"))
            self._logger.error(
                f"Error occurred while trying to execute Terraform. "
                f"Output = {clean_output}"
            )
            if command in ALLOWED_LOGGING_CMDS:
                self._logger.error(f"{command} - {clean_output}")
            raise TerraformExecutionError(
                f"Error during Terraform {command}. "
                f"For details, please, look at the logs.",
                clean_output,
            )
        except Exception as e:
            clean_output = StringCleaner.get_clean_string(str(e))
            self._logger.error(f"Error Running Terraform {command} {clean_output}")
            raise TerraformExecutionError(
                "Error during Terraform Command."
                "For more information please look at the logs."
            )
