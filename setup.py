#!/usr/bin/env python
from typing import List

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


# TODO: Get this working instead of the text lists below.
def get_requirements(test=False) -> List[str]:
    """Returns all requirements for this package."""
    if test:
        with open('requirements_test.txt') as f:
            requirements = f.read().splitlines()
    else:
        with open('requirements.txt') as f:
            requirements = f.read().splitlines()
    return requirements


requirements = [
    "loguru==0.5.3",
    "requests==2.25.1"
                ]

test_requirements = [
    "pip==19.2.3",
    "bump2version==0.5.11",
    "wheel==0.33.6",
    "watchdog==0.9.0",
    "flake8==3.7.8",
    "tox==3.14.0",
    "coverage==4.5.4",
    "Sphinx==1.8.5",
    "twine==1.14.0",
]

setup(
    author="Paul Armstrong",
    author_email='paul_armstrong211@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Small python wrapper for interacting with the Synology Download Station. ",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='download_station_api',
    name='download_station_api',
    packages=find_packages(include=['download_station_api', 'download_station_api.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/paul-armstrong-dev/download_station_api',
    version='0.1.1',
    zip_safe=False,
)
