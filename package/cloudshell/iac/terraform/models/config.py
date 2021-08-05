from typing import Dict


class TerraformShellConfig:
    def __init__(self, write_sandbox_messages: bool = False, update_live_status: bool = False,
                 inputs_map: Dict = None, outputs_map: Dict = None):
        self.write_sandbox_messages = write_sandbox_messages
        self.update_live_status = update_live_status
        self.inputs_map = inputs_map
        self.outputs_map = outputs_map
