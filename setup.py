"""Setup script for atq."""
import glob
import pip
import shlex
import subprocess
import unittest

from distutils import cmd
from setuptools import setup
from setuptools.command.install import install
from pip.download import PipSession
from pip.req import parse_requirements


class RunLintCommand(cmd.Command):
    """Runs linter."""
    description = 'Run linter'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call(shlex.split(
            'pylint --reports=n --rcfile=.pylintrc ' +
            ' '.join(glob.glob('atq/*.py')) + ' ' +
            ' '.join(glob.glob('atq/tests/*.py'))))


class RunDepsInstallCommand(cmd.Command):
    """Installs project dependencies."""
    description = 'Install dependencies'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pip.main(['install', '-r', 'requirements.txt'])


class RunEndToEndTestCommand(cmd.Command):
    """Runs all end to end tests."""
    description = 'Run end to end tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().discover(
            'atq/tests/.', pattern='*.py')
        unittest.TextTestRunner(verbosity=2, buffer=True).run(suite)


class AtqInstall(install):
    """Installs package."""

    def run(self):
        install.run(self)

setup(
    name='atq',
    version='0.0.1',
    packages=['atq'],
    description="Async task queue for Python",
    url='http://github.com/nvdv/atq',
    license='BSD',
    author='nvdv',
    author_email='aflatnine@gmail.com',
    keywords=['task queue', 'asyncio', 'async'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development',
    ],
    entry_points={
        'console_scripts': [
            'atqserver = atq.__main__:main'
        ]
    },
    install_requires=[
        str(req.req) for req in parse_requirements('requirements.txt',
                                                   session=PipSession())
    ],
    python_requires='>=3.5',
    cmdclass={
        'lint': RunLintCommand,
        'test': RunEndToEndTestCommand,
        'deps_install': RunDepsInstallCommand,
    },
)
