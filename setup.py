"""
Setup configuration for AI Podcast Flow
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README_PYTHON.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="ai-podcast-flow",
    version="1.0.0",
    description="Intelligent podcast workflow automation system using Google Agent Development Kit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Podcast Flow Team",
    author_email="team@aipodcastflow.com",
    url="https://github.com/your-org/ai-podcast-flow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "deployment": [
            "gunicorn>=21.2.0",
            "uvicorn[standard]>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aipodflow=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords=[
        "podcast",
        "automation",
        "ai",
        "machine-learning",
        "google-cloud",
        "agent-development-kit",
        "transcription",
        "content-generation",
        "publishing",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-org/ai-podcast-flow/issues",
        "Source": "https://github.com/your-org/ai-podcast-flow",
        "Documentation": "https://github.com/your-org/ai-podcast-flow/blob/main/README_PYTHON.md",
    },
)