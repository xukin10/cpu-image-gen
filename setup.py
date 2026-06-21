from setuptools import setup, find_packages

setup(
    name="cpu-image-gen",
    version="1.0.0",
    author="CPU Image Gen Team",
    description="A powerful prompt builder for AI image generation, supporting Chinese input and cultural entities",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/xukin10/cpu-image-gen",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "diffusers>=0.25.0",
        "transformers>=4.35.0",
        "accelerate>=0.25.0",
        "safetensors>=0.4.0",
        "huggingface_hub>=0.20.0",
    ],
    entry_points={
        "console_scripts": [
            "cpu-image-gen=src.prompt_builder:main",
        ],
    },
)
