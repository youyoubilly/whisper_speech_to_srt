#!/usr/bin/env python3
"""
Whisper API - Simple transcription API for WhisperPal macOS app
Takes an audio file path and model name, outputs plain text transcription to stdout.
"""

import whisper
import sys
import os
from pathlib import Path

def transcribe_audio(audio_file: str, model_name: str = "base") -> str:
    """
    Transcribe audio file using Whisper model.
    
    Args:
        audio_file: Path to audio file
        model_name: Whisper model name (base, large-v3, etc.)
    
    Returns:
        Plain text transcription (concatenated segments)
    """
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load Whisper model
        print(f"Loading Whisper model ({model_name})...", file=sys.stderr)
        model = whisper.load_model(model_name)
        
        # Transcribe
        print(f"Transcribing {audio_file}...", file=sys.stderr)
        result = model.transcribe(audio_file, verbose=False)
        
        # Extract and concatenate text from segments
        segments = result.get('segments', [])
        text_parts = [segment['text'].strip() for segment in segments if segment.get('text')]
        transcription = ' '.join(text_parts)
        
        return transcription
        
    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: whisper_api.py <audio_file> [model_name]", file=sys.stderr)
        print("  audio_file: Path to audio file to transcribe", file=sys.stderr)
        print("  model_name: Whisper model name (default: base)", file=sys.stderr)
        sys.exit(1)
    
    audio_file = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    try:
        transcription = transcribe_audio(audio_file, model_name)
        # Output transcription to stdout (no stderr messages)
        print(transcription, end='')
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
