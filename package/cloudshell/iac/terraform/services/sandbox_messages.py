from cloudshell.api.cloudshell_api import CloudShellAPISession


class SandboxMessagesService:
    def __init__(self, api: CloudShellAPISession, sandbox_id: str, service_name: str, write_messages_to_sandbox: bool):
        self._api = api
        self._sandbox_id = sandbox_id
        self._service_name = service_name
        self._write_messages_to_sandbox = write_messages_to_sandbox

    def write_message(self, message: str, prefix: str = "", postfix: str = ""):
        if self._write_messages_to_sandbox:
            formatted_message = self._format_message(self._service_name, message)
            self._api.WriteMessageToReservationOutput(self._sandbox_id, f'{prefix}{formatted_message}{postfix}')

    def _format_message(self, service_name, message):
        if ' ' in service_name:
            service_name = '"{0}"'.format(service_name)
        return '{0} {1}'.format(service_name, message)

    def write_error_message(self, message: str):
        prefix = '<font color="red">'
        postfix = '</font>'
        self.write_message(message, prefix, postfix)
