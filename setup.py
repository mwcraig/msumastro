from setuptools import setup, find_packages
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
    version='FIXME',
    description='Process FITS files painlessly',
    url='http://github.com/mwcraig/msumastro',
    long_description=(open('README.rst').read()),
    license='BSD 3-clause',
    author='Matt Craig',
    author_email='mcraig@mnstate.edu',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=['astropysics>=0.0.dev0',
                      'astropy',
                      'numpy'],
    extras_require={
        'testing': ['pytest>1.4', 'pytest-capturelog'],
        'docs': ['numpydoc', 'sphinx-argparse']
    },
    entry_points={
        'console_scripts': [
            ('quick_add_keys_to_file.py = '
             'msumastro.scripts.quick_add_keys_to_file:main'),
            ('run_patch.py = '
             'msumastro.scripts.run_patch:main'),
            ('run_astrometry.py = '
             'msumastro.scripts.run_astrometry:main')
        ]
    },
    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: BSD License',
                 'Programming Language :: Python :: 2 :: Only']
    )
