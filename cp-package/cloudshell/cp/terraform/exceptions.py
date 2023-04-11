# from collections.abc import Iterable


class BaseTFException(Exception):
    pass


class InvalidCommandParam(BaseTFException):
    def __init__(
        self, param_name: str, param_value: str, expected_values  # Iterable[str]
    ):
        self.param_name = param_name
        self.param_value = param_value
        self.expected_values = expected_values
        super().__init__(
            f"Param '{param_name}' is invalid. It should be one of the "
            f"'{expected_values}' but the value is '{param_value}'"
        )


class InvalidAppParamValue(BaseTFException):
    """Deploy App variables conversion Exception."""


class InvalidResourceAttributeValue(BaseTFException):
    """Deploy App variables conversion Exception."""


class LoginException(BaseTFException):
    """Login Exception."""


class InvalidAttributeException(BaseTFException):
    """Attribute is not valid."""


class VMIPNotFoundException(BaseTFException):
    """Object not found."""
