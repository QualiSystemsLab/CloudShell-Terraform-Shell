@echo off
cd shells\generic_terraform_shell
shellfoundry install
cd ..\..\package
python setup.py sdist
cd dist
xcopy /Q /Y . "C:\Program Files (x86)\QualiSystems\CloudShell\Server\Config\Pypi Server Repository"
cd ..\..