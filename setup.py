from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='msumastro',
    version='IXME',
    description='Process FITS files painlessly',
    long_description=(open('README.rst').read()),
    license='BSD 3-clause',
    author='Matt Craig',
    author_email='mcraig@mnstate.edu',
    packages=['msumastro'],
    include_package_data=True,
    install_requires=['astropysics>=0.0.dev0',
                      'astropy',
                      'numpy'],
    extras_require={
        'testing': ['pytest', 'pytest-capturelog']
    },
    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: BSD License',
                 'Programming Language :: Python :: 2 :: Only']
     )
