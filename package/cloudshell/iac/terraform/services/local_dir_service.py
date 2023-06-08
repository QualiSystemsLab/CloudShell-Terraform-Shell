import logging
import os
import shutil
from pathlib import Path

from cloudshell.iac.terraform.constants import ATTRIBUTE_NAMES
from cloudshell.iac.terraform.downloaders.downloader import Downloader
from cloudshell.iac.terraform.models.shell_helper import ShellHelperObject
from cloudshell.iac.terraform.services.sandox_data import SandboxDataHandler


def handle_remove_readonly(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat

    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def validate_tf_exe(exe_path: str):
    if not os.path.isfile(exe_path):
        raise ValueError(f"Local TF exe not found at path: '{exe_path}'")


class LocalDir:
    @staticmethod
    def delete_local_temp_dir(
        sandbox_data_handler: SandboxDataHandler, tf_working_dir: str
    ):
        tf_path = Path(tf_working_dir)
        tmp_folder_found = False
        while not tmp_folder_found:
            objects_in_folder = os.listdir(tf_path.parent.absolute())
            if len(objects_in_folder) == 2:
                if "REPO" in objects_in_folder and "repo.zip" in objects_in_folder:
                    tmp_folder_found = True
            tf_path = Path(tf_path.parent.absolute())
        tf_path_str = str(tf_path)
        shutil.rmtree(tf_path_str, onerror=handle_remove_readonly)
        sandbox_data_handler.set_tf_working_dir("")

    @staticmethod
    def does_working_dir_exists(working_dir: str) -> bool:
        return working_dir and os.path.isdir(working_dir)

    @staticmethod
    def prepare_tf_working_dir(
        logger: logging.Logger,
        sandbox_data_handler: SandboxDataHandler,
        shell_helper: ShellHelperObject,
    ):
        tf_working_dir = sandbox_data_handler.get_tf_working_dir()

        if not (tf_working_dir and os.path.isdir(tf_working_dir)):
            # working dir doesnt exist - need to download repo and tf exec
            downloader = Downloader(shell_helper)
            tf_working_dir = downloader.download_terraform_module()

            local_tf_exe = shell_helper.attr_handler.get_attribute(
                ATTRIBUTE_NAMES.LOCAL_TERRAFORM
            )

            # if offline, can copy local terraform exe (must exist already on ES)
            if local_tf_exe:
                validate_tf_exe(local_tf_exe)
                logger.info(f"Copying Local TF exe: '{local_tf_exe}'")
                shutil.copy(local_tf_exe, tf_working_dir)
            else:
                downloader.download_terraform_executable(tf_working_dir)

            sandbox_data_handler.set_tf_working_dir(tf_working_dir)
        else:
            logger.info(f"Using existing working dir = {tf_working_dir}")
        return tf_working_dir
