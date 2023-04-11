import os

from setuptools import find_packages, setup

with open(os.path.join("version.txt")) as version_file:
    version_from_file = version_file.read().strip()

with open("requirements.txt") as f_required:
    required = f_required.read().splitlines()

with open("test_requirements.txt") as f_tests:
    required_for_tests = f_tests.read().splitlines()

setup(
    name="cloudshell-cp-terraform",
    url="http://www.qualisystems.com/",
    author="QualiSystems",
    author_email="info@qualisystems.com",
    packages=find_packages(),
    description=(
        "This Shell enables setting up TF as a cloud provider in CloudShell. It "
        "supports connectivity, and adds new deployment types for apps which can be "
        "used in CloudShell sandboxes."
    ),
    long_description=(
        "This Shell enables setting up TF as a cloud provider in CloudShell. It "
        "supports connectivity, and adds new deployment types for apps which can be "
        "used in CloudShell sandboxes."
    ),
    install_requires=required,
    tests_require=required_for_tests,
    python_requires="~=3.9",
    version=version_from_file,
    package_data={"": ["*.txt"]},
    include_package_data=True,
)
