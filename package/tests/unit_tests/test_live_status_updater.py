import unittest

from mock import Mock

from cloudshell.iac.terraform.services.live_status_updater import LiveStatusUpdater


class TestLiveStatusUpdater(unittest.TestCase):
    def test_live_status_no_update(self):
        # arrange
        api = Mock()
        updater = LiveStatusUpdater(api, Mock(), False)

        # act
        updater.set_service_live_status("service name", "Online", "description...")

        # assert
        api.SetServiceLiveStatus.assert_not_called()

    def test_write_message(self):
        # arrange
        sandbox_id = Mock()
        api = Mock()
        updater = LiveStatusUpdater(api, sandbox_id, True)

        # act
        updater.set_service_live_status("service name", "Online", "description...")

        # assert
        api.SetServiceLiveStatus.assert_called_with(sandbox_id, "service name", "Online", "description...")
