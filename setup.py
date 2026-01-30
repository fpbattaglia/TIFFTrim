from setuptools import find_packages, setup

setup(
    name="tifftrim",
    version="0.1.0",
    description="Trim 3D TIFF stacks while preserving TIFF tags/metadata",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "tifffile>=2023.0.0",
    ],
    entry_points={
        "console_scripts": [
            "tifftrim=tifftrim.cli:main",
        ]
    },
)
