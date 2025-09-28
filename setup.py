#!/usr/bin/env python3
"""
Setup script for Mental Health Agent
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="mental-health-agent",
    version="1.0.0",
    author="Mental Health Agent Team",
    author_email="contact@mentalhealthagent.com",
    description="A comprehensive mental health support system built with AWS Bedrock and Lambda functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mental_health_agent_starter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "mental-health-agent=scripts.invoke_mental_health_agent:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
