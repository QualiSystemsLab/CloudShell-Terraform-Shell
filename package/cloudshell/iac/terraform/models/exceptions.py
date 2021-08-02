class TerraformExecutionError(Exception):
    def __init__(self, message, std_out=""):
        self.message = message + std_out
        super().__init__(self.message)


class TerraformAutoTagsError(Exception):
    def __init__(self, message, std_out=""):
        self.message = message + std_out
        super().__init__(self.message)
