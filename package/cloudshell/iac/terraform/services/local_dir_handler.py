import os
import shutil
from pathlib import Path


def delete_local_temp_dir(sandbox_data_handler, tf_working_dir):
    tf_path = Path(tf_working_dir)
    tmp_folder_found = False
    while not tmp_folder_found:
        objects_in_folder = os.listdir(tf_path.parent.absolute())
        if len(objects_in_folder) == 2:
            if objects_in_folder[0] == 'REPO' and objects_in_folder[1] == 'repo.zip':
                tmp_folder_found = True
        tf_path = Path(tf_path.parent.absolute())
    tf_path_str = str(tf_path)
    shutil.rmtree(tf_path_str)
    sandbox_data_handler.set_tf_working_dir("")
