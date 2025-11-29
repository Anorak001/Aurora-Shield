"""Setup script for Aurora Shield."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aurora-shield",
    version="1.0.0",
    author="Aurora Shield Team",
    description="A lightweight, modular DDoS protection framework for cloud applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anorak001/Aurora-Shield",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.0",
        "numpy>=1.24.0",
        "boto3>=1.26.0",
    ],
    entry_points={
        "console_scripts": [
            "aurora-shield=main:main",
        ],
    },
)
