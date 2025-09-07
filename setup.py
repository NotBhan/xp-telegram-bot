#!/usr/bin/env python3
"""
Setup script for XP Telegram Bot
"""

from setuptools import setup, find_packages
import os

# Read the README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="xp-telegram-bot",
    version="1.0.0",
    description="A gamified Telegram bot for tracking XP, quests, and productivity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="XP Bot Development Team",
    author_email="dev@xpbot.com",
    url="https://github.com/your-username/xp-telegram-bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
        "Topic :: Office/Business :: Scheduling",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "xp-bot=bot:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="telegram bot gamification productivity xp quests notion",
    project_urls={
        "Bug Reports": "https://github.com/your-username/xp-telegram-bot/issues",
        "Source": "https://github.com/your-username/xp-telegram-bot",
        "Documentation": "https://github.com/your-username/xp-telegram-bot#readme",
    },
)