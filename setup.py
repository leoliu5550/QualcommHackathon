from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fileorg",
    version="1.0.0",
    author="NameByLeader",
    author_email="leoliu5550@gmail.com",
    description="智慧檔案整理工具 - 使用 AI 技術自動分類與整理檔案",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leoliu5550/QualcommHackathon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "qualcomm": [
            "qai-hub",
        ],
    },
    entry_points={
        "console_scripts": [
            "fileorg=fileorg.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fileorg": ["**/*.json", "**/*.yaml", "**/*.md"],
    },
)