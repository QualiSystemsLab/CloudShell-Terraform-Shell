@echo off
cd shells\generic_terraform_service
shellfoundry install
cd ..\..\package
python setup.py sdist
cd dist
xcopy /Q /Y . "C:\Program Files (x86)\QualiSystems\CloudShell\Server\Config\Pypi Server Repository"
cd ..\..
cd shells\backends\azure_tf_backend
shellfoundry install
cd ..\..
cd backends\aws_tf_backend
shellfoundry install
cd ..\..\..
cd backends\gcp_tf_backend
shellfoundry install
cd ..\..\..
