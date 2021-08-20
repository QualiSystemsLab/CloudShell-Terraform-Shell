from setuptools import setup, find_packages
import os

with open(os.path.join('version.txt')) as version_file:
    version_from_file = version_file.read().strip()

with open('requirements.txt') as f_required:
    required = f_required.read().splitlines()

with open('test_requirements.txt') as f_tests:
    required_for_tests = f_tests.read().splitlines()

setup(
    name="cloudshell-iac-terraform",
    author="QualiLabs",
    author_email="support@qualisystems.com",
    description="Allow execution of Terraform modules from CloudShell",
    packages=find_packages(),
    test_suite='nose.collector',
    test_requires=required_for_tests,
    package_data={'': ['*.txt']},
    install_requires=required,
    version=version_from_file,
    include_package_data=True,
    keywords="sandbox cloud IaC cloudshell terraform",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
    ],
    requires=[]
)
