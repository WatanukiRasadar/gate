class ContainerException(Exception): pass


class ServiceNotFountException(ContainerException):

    def __init__(self, service_name: str) -> None:
        super().__init__(f'the service "{service_name}" not found')


class ParameterNotDefinedException(ContainerException):

    def __init__(self, parameter_name: str) -> None:
        super().__init__(f'the parameter "{parameter_name}" is not defined')


class ServiceConfigurationException(ContainerException):

    def __init__(self, service_name: str) -> None:
        super().__init__(f'invalid configuration to service "{service_name}"')
