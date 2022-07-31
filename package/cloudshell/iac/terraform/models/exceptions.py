class TerraformExecutionError(Exception):
    def __init__(self, message, std_out=""):
        self.message = message + std_out
        super().__init__(self.message)


class TerraformOPAPolicyValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)


class TerraformAutoTagsError(Exception):
    def __init__(self, message, std_out=""):
        self.message = message + std_out
        super().__init__(self.message)
