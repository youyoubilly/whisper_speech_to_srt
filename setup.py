#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="whisper-speech-to-srt",
    version="1.0.0",
    description="Convert audio/video to SRT subtitles using Whisper",
    author="Billy Wang",
    py_modules=["whisper_speech_to_srt", "srt_to_txt", "srt_to_lrc"],
    install_requires=[
        "openai-whisper",
    ],
    entry_points={
        "console_scripts": [
            "whisper-srt=whisper_speech_to_srt:main",
            "srt2txt=srt_to_txt:main",
            "srt2lrc=srt_to_lrc:main",
        ],
    },
    python_requires=">=3.8",
)

