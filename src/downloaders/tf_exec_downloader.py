import json
import os
import re
import sys
import traceback
from io import BytesIO
from logging import Logger
from urllib.request import Request, urlopen
from zipfile import ZipFile

from constants import TERRAFORM_LATEST_URL, OS_TYPES, TERRAFORM_URL


class TfExecDownloader(object):
    def __init__(self, logger: Logger):
        self.logger = logger

    def download_terraform_executable(tf_workingdir: str, version='latest'):
        # Must be in format of d.dd.dd and cannot have 0 in front of a number like 0.05.05, this is valid 0.5.0
        valid_version_regex = re.compile('^([0-9]{1})\.([1-9]{0,1}[0-9]{1})\.([1-9]{0,1}[0-9]{1})$')

        if not version:
            version = 'latest'
        # Grabs the latest version of terraform from the hashicorp site
        if version == 'latest':
            try:
                tfurl = TERRAFORM_LATEST_URL
                req = Request(tfurl)
                tfresponse = urlopen(req).read()
            except Exception:
                raise ValueError('generic exception: ' + traceback.format_exc())
            cont = json.loads(tfresponse.decode('utf-8'))
            if 'current_version' in cont.keys():
                version = cont['current_version']
            else:
                raise ValueError(f'Could not find latest TF version from hashicorp site')

        # Verifying values
        if not os.path.exists(tf_workingdir):
            raise ValueError(f'Target path: {tf_workingdir} does not exist. Cannot be sym link.')
        if valid_version_regex.match(version) is None:
            raise ValueError(f'Version {version} is not a valid format. examples 1.0.0, 0.15.2, 0.12.15')
        if sys.platform not in OS_TYPES:
            raise ValueError('Could not find OS type. Must be 64 bit and Windows, Ubuntu, or CentOS/Redhat.')

        os_type = OS_TYPES[sys.platform]
        # Downloads and unzips files in memory, then outputs exe to path
        try:
            zipurl = f'{TERRAFORM_URL}/{version}/terraform_{version}_{os_type}.zip'
            with urlopen(zipurl) as zipresp:
                with ZipFile(BytesIO(zipresp.read())) as zfile:
                    zfile.extractall(tf_workingdir)
        except Exception as e:
            raise ValueError('generic exception: ' + str(e))

        # Linux systems do not add .exe but windows does, adding .exe so commands will be the same on all OS's
        if os.path.exists(f'{tf_workingdir}/terraform'):
            os.rename(f'{tf_workingdir}/terraform', f'{tf_workingdir}/terraform.exe')
        os.chmod(f'{tf_workingdir}/terraform.exe', 0o755)

