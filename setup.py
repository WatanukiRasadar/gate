from setuptools import find_packages, setup

setup(
    name='gate',
    version='0.1',
    packages=['gate'],
    url='',
    license='MIT',
    author='elielton kremer',
    author_email='elielton@uoou.com.br',
    description='Steins Gate',
    entry_points={
        'console_scripts' : {
            'pip=gate.internal:main'
        }
    }
)
