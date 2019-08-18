from argparse import ArgumentParser, REMAINDER
from abc import abstractmethod, ABC
from importlib import import_module
from os import environ


class AbstractCommand(ABC):

    @abstractmethod
    def define_arguments(self, parser: ArgumentParser): pass

    @property
    def arguments(self):
        parser = ArgumentParser()
        self.define_arguments(parser)
        return parser.parse_known_args()[0]

    @abstractmethod
    def execute(self): pass


class ApplicationCommand(AbstractCommand):

    @property
    def container(self):
        from .container import ApplicationContainer
        if not hasattr(self, '_container'):
            settings = import_module(self.arguments.config)
            setattr(self, '_container',  ApplicationContainer(settings))
        return getattr(self, '_container')

    def define_arguments(self, parser):
        parser.add_argument('--command', help='Type a command to execute', default=None)
        parser.add_argument('--config', help='Tyoe a config module path', required=True)

    def execute(self):
        if self.arguments.command:
            command: AbstractCommand = self.container.get_service(f'console.commands.{self.arguments.command}')
            return command.execute()
