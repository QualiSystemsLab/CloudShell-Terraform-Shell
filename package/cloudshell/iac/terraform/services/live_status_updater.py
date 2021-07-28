from cloudshell.api.cloudshell_api import CloudShellAPISession


class LiveStatusUpdater:
    def __init__(self, api: CloudShellAPISession, sandbox_id: str, update_live_status: bool):
        self._api = api
        self._sandbox_id = sandbox_id
        self._update_live_status = update_live_status

    def set_service_live_status(self, service_name: str, status: str, description: str) -> None:
        if self._update_live_status:
            self._api.SetServiceLiveStatus(
                self._sandbox_id,
                service_name,
                status,
                description
            )
