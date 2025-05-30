from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="libgen-explorer",
    version="0.1.0",
    author="Ray Zhang, Ian Jiang",
    author_email="rui.zhang@sjsu.edu, jisheng.jiang@sjsu.edu",
    description="A Python tool to search and analyze LibGen resources using GUN database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/libgen-explorer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "libgen-explorer=libgen_explorer.cli:main",
        ],
    },
)