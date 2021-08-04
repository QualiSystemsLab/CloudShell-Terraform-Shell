@echo off
cd shells\generic_terraform_service
shellfoundry install
cd ..\..\package
python setup.py sdist
cd dist
