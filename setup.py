#!/usr/bin/env python

"""The setup script."""
import os
from setuptools import setup, find_packages


ROOT = os.path.dirname(os.path.realpath(__file__))

package_name = "simseqgen"

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [""]

test_requirements = [
    "pytest>=3",
]

package_data = []


def package_path(path, filters=()):
    if not os.path.exists(path):
        raise RuntimeError("packaging non-existent path: %s" % path)
    elif os.path.isfile(path):
        package_data.append(os.path.relpath(path, package_name))
    else:
        for path, dirs, files in os.walk(path):
            path = os.path.relpath(path, package_name)
            for f in files:
                if not filters or f.endswith(filters):
                    package_data.append(os.path.join(path, f))


package_path(os.path.join(ROOT, package_name, "data"))

setup(
    author="Per Unneberg",
    author_email="per.unneberg@scilifelab.se",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Simulate genealogy and read sequences",
    entry_points={
        "console_scripts": [
            "simseqgen=simseqgen.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="simseqgen",
    name="simseqgen",
    packages=find_packages(include=["simseqgen", "simseqgen.*"]),
    package_data={"simseqgen/data": package_data},
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/percyfal/simseqgen",
    version="0.1.0",
    zip_safe=False,
    use_scm_version={"write_to": "simseqgen/_version.py"},
)
