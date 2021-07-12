class TerraformShellConfig:
    def __init__(self, write_sandbox_messages: bool = False, update_live_status: bool = False):
        self.write_sandbox_messages = write_sandbox_messages
        self.update_live_status = update_live_status

