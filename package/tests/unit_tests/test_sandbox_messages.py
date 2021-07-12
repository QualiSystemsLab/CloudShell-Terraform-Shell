import unittest

from mock import Mock

from cloudshell.iac.terraform.services.sandbox_messages import SandboxMessagesService


class TestSandboxMessagesService(unittest.TestCase):
    def test_messages_suppressed(self):
        # arrange
        api = Mock()
        messages_service = SandboxMessagesService(api, Mock(), Mock(), False)

        # act
        messages_service.write_message("some message")

        # assert
        api.WriteMessageToReservationOutput.assert_not_called()

    def test_write_message(self):
        # arrange
        api = Mock()
        sandbox_id = Mock()
        messages_service = SandboxMessagesService(api, sandbox_id, "my service", True)

        # act
        messages_service.write_message("my msg")

        # assert
        api.WriteMessageToReservationOutput.assert_called_with(sandbox_id, '"my service" my msg')
