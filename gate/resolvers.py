import re
from importlib import import_module
from re import match
from typing import Union, Callable, Any

from gate.exceptions import ServiceConfigurationException, ParameterNotDefinedException
from .container import AbstractContainer


class ServiceResolver:

    def __init__(self, container: AbstractContainer):
        self.container = container

    def _resolve_factory(self, service_name: str, configuration: dict):
        if 'class' in configuration.keys():
            module, class_name = configuration.get('class', '').split(':')
            return getattr(import_module(module), class_name)
        if 'factory' in configuration.keys():
            factory = configuration.get('factory')
            if callable(factory):
                return factory
            elif isinstance(factory, str):
                return self.container.get_service(factory)
        raise ServiceConfigurationException(service_name)

    def resolve(self, service_name: str, configuration: dict):
        factory: Union[type, Callable] = self._resolve_factory(service_name, configuration)
        parameters = configuration.get('parameters', {})
        for parameter_name, parameter_value in parameters.items():
            if isinstance(parameter_value, str) and match(r'^(\w+)::', parameter_value):
                parameters[parameter_name] = self.container.get_parameter(parameter_value)
        return factory(**parameters)


class ParameterResolver:

    def __init__(self, container: AbstractContainer):
        self.container = container

    def _recursive_resolve(self, value: Any):
        if isinstance(value, dict):
            return {k: self._recursive_resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._recursive_resolve(v) for v in value]
        if isinstance(value, str):
            if value.startswith('parameter::'):
                return self.container.get_parameter(value.replace('parameter::', ''))
            if value.startswith('service::'):
                return self.container.get_service(value.replace('service::', '', 1))
            match = re.match(r'^(\w+)::', value)
            if match and match.group():
                if self.container.has_service(f'container.{match.group()}_resolver'):
                    resolver = self.container.get_service(f'container.{match.group()}_resolver')
                    return resolver.resolve(value)
                else:
                    raise ParameterNotDefinedException(value)
        return value

    def resolve(self, parameter_value: Any):
        response = self._recursive_resolve(parameter_value)
        if not isinstance(response, ParameterResponse):
            response = ParameterResponse(response)
        return response


class ParameterResponse:

    def __init__(self, value: Any, persist: bool = False):
        self.value = value
        self.persist = persist
