from setuptools import setup, find_packages

setup(
    name="FileOrganizerPro",
    version="2.0.0",
    author="David - JSMS Academy",
    author_email="support@jsmsacademy.com",
    description="Professional File Organization & Duplicate Management System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://www.jsmsacademy.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Filesystems",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=9.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fileorganizer=file_organizer_pro:main",
        ],
    },
)
