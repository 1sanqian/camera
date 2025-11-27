#!/usr/bin/env python3
"""
Setup script for 4-Camera Monitoring System
"""

from setuptools import setup, find_packages

setup(
    name="camera-monitor",
    version="1.0.0",
    description="4-Camera Monitoring System for Ubuntu",
    author="Your Name",
    author_email="your.email@example.com",
    py_modules=["main"],
    install_requires=[
        "PyQt6>=6.6.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "camera-monitor=main:main",
        ],
    },
    python_requires=">=3.8",
)

