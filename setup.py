from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

import versioneer

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

INSTALL_REQUIRES = ['astropy>=1.0', 'numpy', 'ccdproc>=1.0']

versioneer_cmdclass = versioneer.get_cmdclass()
versioneer_cmdclass['test'] = PyTest
setup(
    name='msumastro',
    version=versioneer.get_version(),
    description='Process FITS files',
    url='http://github.com/mwcraig/msumastro',
    long_description=(open('README.rst').read()),
    license='BSD 3-clause',
    author='Matt Craig',
    author_email='mcraig@mnstate.edu',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'docs': ['numpydoc', 'sphinx-argparse', 'sphinx_rtd_theme', 'astropy-helpers'],
    },
    tests_require=['scipy', 'pytest>=2.9', 'pytest-capturelog'] + INSTALL_REQUIRES,
    cmdclass=versioneer_cmdclass,
    entry_points={
        'console_scripts': [
            ('quick_add_keys_to_file.py = '
             'msumastro.scripts.quick_add_keys_to_file:main'),
            ('run_patch.py = '
             'msumastro.scripts.run_patch:main'),
            ('run_astrometry.py = '
             'msumastro.scripts.run_astrometry:main'),
            ('run_triage.py = '
             'msumastro.scripts.run_triage:main'),
            ('run_standard_header_process.py = '
             'msumastro.scripts.run_standard_header_process:main'),
            ('sort_files.py = '
             'msumastro.scripts.sort_files:main')
        ]
    },
    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: BSD License',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 2 :: Only',
                 'Intended Audience :: Science/Research',
                 'Topic :: Scientific/Engineering :: Astronomy'],
    )
