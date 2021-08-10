#!/bin/bash

cd package
python setup.py sdist
cd dist
# package_name=$(find ./ -maxdepth 1 -type f -name "cloudshell-iac-terraform-*.tar.gz" -printf "%f\n")
pip install --no-index -f . cloudshell-iac-terraform
cd ../..
