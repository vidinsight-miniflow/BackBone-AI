"""
Setup script for BackBone-AI.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="backbone-ai",
    version="0.1.0",
    author="VidInsight MiniFlow",
    description="AI-driven code generation for FastAPI and SQLAlchemy backends",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vidinsight-miniflow/BackBone-AI",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "backbone-ai=app.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["templates/*.jinja2"],
    },
)
