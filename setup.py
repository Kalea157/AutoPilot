#!/usr/bin/env python3
"""
Setup-Script für das E-Mail-Agent-System
"""

from setuptools import setup, find_packages
import os

# Lese README-Datei
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Lese Requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="email-agent-system",
    version="1.0.0",
    author="E-Mail Agent System",
    author_email="support@email-agent.com",
    description="Ein autonomer KI-E-Mail-Agent mit Telegram-Integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/email-agent-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Email",
        "Topic :: Internet",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.10",
        ],
    },
    entry_points={
        "console_scripts": [
            "email-agent=main:main",
            "email-agent-test=test_system:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="email, ai, telegram, automation, gpt, openai, imap, smtp",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/email-agent-system/issues",
        "Source": "https://github.com/yourusername/email-agent-system",
        "Documentation": "https://github.com/yourusername/email-agent-system#readme",
    },
)