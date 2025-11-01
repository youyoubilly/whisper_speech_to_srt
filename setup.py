#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="whisper-speech-to-srt",
    version="1.0.0",
    description="Convert audio/video to SRT subtitles using Whisper",
    author="Billy Wang",
    py_modules=["whisper_speech_to_srt"],
    install_requires=[
        "openai-whisper",
    ],
    entry_points={
        "console_scripts": [
            "whisper-srt=whisper_speech_to_srt:main",
        ],
    },
    python_requires=">=3.8",
)

