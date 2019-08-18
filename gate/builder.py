from typing import Any

from yaml import safe_load

from .container import Container


class ContainerBuilder:

    def __init__(self):
        self._configuration = {}

    def service(self, name: str, callback=None, parameters: dict = None):
        parameters = parameters or {}
        if callback is None:
            def wrapper(callback):
                self._configuration.setdefault('services', {})[name] = {
                    'factory': callback,
                    'parameters': parameters
                }
                return callback
            return wrapper
        else:
            self._configuration.setdefault('services', {})[name] = {
                'factory': callback,
                'parameters': parameters
            }
            return self

    def parameter(self, name: str, value: Any):
        self._configuration.setdefault('parameters', {})[name] = value
        return self

    def file(self, path: str):
        with open(path) as configuration_file:
            configuration = safe_load(configuration_file)
            self._configuration.setdefault('parameters', {}).update(configuration.get('parameters', {}))
            self._configuration.setdefault('services', {}).update(configuration.get('services', {}))
        return self

    def create(self):
        container = Container(
            parameters=self._configuration.get('parameters'),
            services=self._configuration.get('services')
        )
        self._configuration = {}
        return container
