from setuptools import setup, find_packages

setup(
    name="agent-budget-guard",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        # 2026 standard AI libraries (placeholders if needed)
    ],
    author="Water Woods & ZQ",
    description="Autonomous AI agent cost monitoring and budget enforcement tool.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/woodwater2026/agent-budget-guard",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
