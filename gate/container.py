from _contextvars import ContextVar
from importlib import import_module
from typing import Generic, TypeVar, List, Dict, Any
from abc import abstractmethod, ABC
from os import path
from yaml import safe_load
from gate.exceptions import ServiceNotFountException, ParameterNotDefinedException


class AbstractContainer(ABC):

    @abstractmethod
    def has_service(self, name: str): pass

    @abstractmethod
    def has_parameter(self, name: str): pass

    @abstractmethod
    def get_service(self, name: str): pass

    @abstractmethod
    def get_parameter(self, name: str): pass


class Container(AbstractContainer):

    def __init__(self, parameters: Dict[str, Any] = None, services: Dict[str, Dict] = None):
        self._parameters = parameters or {}
        self._services = services or {}

    def has_service(self, name: str):
        return name in self._services.keys()

    def has_parameter(self, name: str):
        return name in self._parameters.keys()

    def get_service(self, name: str):
        if not self.has_service(name):
            raise ServiceNotFountException(name)
        return self._services.get(name)

    def get_parameter(self, name: str):
        if not self.has_parameter(name):
            raise ParameterNotDefinedException(name)
        return self._parameters.get(name)


class ContainerStack(AbstractContainer):

    def __init__(self, containers: List[AbstractContainer] = None):
        self._containers = containers or []
        self._services = {}
        self._parameters = {}

    def has_service(self, name: str):
        return name in self._services.keys() or any((container.has_service(name) for container in self._containers))

    def has_parameter(self, name: str):
        return name in self._parameters.keys() or any((container.has_parameter(name) for container in self._containers))

    def get_service(self, name: str):
        service = self._services.get(name)
        if service is None:
            for container in self._containers:
                if container.has_service(name):
                    service = container.get_service(name)
                    break
        if service is None:
            raise ServiceNotFountException(name)
        else:
            self._services[name] = service
        return service

    def get_parameter(self, name: str):
        parameter = self._parameters.get(name)
        if parameter is None:
            for container in self._containers:
                if container.has_parameter(name):
                    parameter = container.get_parameter(name)
                    break
        if parameter is None:
            raise ParameterNotDefinedException(name)
        else:
            self._parameters[name] = parameter
        return parameter


class ContextContainer(AbstractContainer):

    def __init__(self, container: AbstractContainer):
        self._container = container
        self.services_instances = {}
        self.runtime_parameters = {}

    def has_service(self, name: str):
        return name in self.services_instances.keys() or self._container.has_service(name)

    def has_parameter(self, name: str):
        return name in self.runtime_parameters.keys() or self._container.has_parameter(name)

    def get_service(self, name: str):
        if 'container' == name:
            return self
        if name not in self.services_instances.keys():
            from .resolvers import ServiceResolver
            service_resolver = ServiceResolver(self)
            self.services_instances[name] = service_resolver.resolve(name, self._container.get_service(name))
        return self.services_instances.get(name)

    def get_parameter(self, name: str):
        if name not in self.runtime_parameters.keys():
            from .resolvers import ParameterResolver
            parameter_resolver = ParameterResolver(self)
            parameter = parameter_resolver.resolve(name)
            if parameter.persist:
                self.runtime_parameters[name] = parameter.value
            else:
                return parameter.value
        return self.runtime_parameters.get(name)


class ApplicationContainer(AbstractContainer):

    def __init__(self, settings, container: AbstractContainer = None):
        self._instance = ContextVar('instance', default=container)
        self._settings = settings

    @property
    def instance(self) -> ContextContainer:
        if self._instance.get() is None:
            containers = []
            for module in getattr(self._settings, 'MODULES', []):
                try:
                    container = getattr(import_module(f'{module}.container'), 'default')
                except:
                    container = None
                if container is None:
                    file_path = path.join(*module.split('.'), 'service.yml')
                    if path.exists(file_path):
                        with open(file_path) as file_config:
                            configuration = safe_load(file_config)
                            container = Container(**configuration)
                if container is not None:
                    containers.append(container)
            context_container = ContextContainer(ContainerStack(list(reversed(containers))))
            if self._settings:
                context_container.runtime_parameters['settings'] = self._settings
            self._instance.set(context_container)
        return self._instance.get()

    def has_service(self, name: str):
        return name == 'container' or self.instance.has_service(name)

    def has_parameter(self, name: str):
        return self.instance.has_parameter(name)

    def get_service(self, name: str):
        return self.instance.get_service(name)

    def get_parameter(self, name: str):
        return self.instance.get_parameter(name)
